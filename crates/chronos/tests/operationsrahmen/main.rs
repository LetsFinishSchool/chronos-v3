//! Tests des Operationsrahmens (ADR-005, ADR-009) gegen echtes PostgreSQL.
//! Voraussetzung: `docker compose up --wait` und `DATABASE_URL`.

mod beispiel;

use chronos_core::{
    ActorKind, Environment, ErrorCode, Frame, Principal, Run, registered_operations,
};
use serde_json::{Value, json};
use sqlx::PgPool;
use uuid::Uuid;

use beispiel::SETUP_SQL;

async fn setup(pool: &PgPool) -> (Frame, Principal) {
    sqlx::query(SETUP_SQL).execute(pool).await.unwrap();
    let frame = Frame::new(pool.clone(), Environment::Test);
    let principal = frame.test_principal().await.unwrap();
    (frame, principal)
}

async fn count(pool: &PgPool, table: &str) -> i64 {
    let sql = match table {
        "example_note" => "SELECT count(*) FROM example_note",
        "history" => "SELECT count(*) FROM history",
        "outbox" => "SELECT count(*) FROM outbox",
        "person" => "SELECT count(*) FROM person",
        other => panic!("unknown table {other}"),
    };
    sqlx::query_scalar(sql).fetch_one(pool).await.unwrap()
}

fn create_params(owner: Principal) -> Value {
    json!({ "owner": owner.id(), "text": "Hello" })
}

mod operationsrahmen {
    use super::*;

    #[sqlx::test]
    async fn change_history_and_event_share_one_transaction(pool: PgPool) {
        let (frame, principal) = setup(&pool).await;
        let correlation_id = Uuid::new_v4();

        let outcome = frame
            .execute(
                &principal,
                "notes.create",
                create_params(principal),
                correlation_id,
                Run::Apply,
            )
            .await
            .unwrap();

        assert!(outcome.applied);
        let note_id: Uuid = serde_json::from_value(outcome.result["id"].clone()).unwrap();
        assert_eq!(count(&pool, "example_note").await, 1);

        let history: (
            Uuid,
            String,
            String,
            Uuid,
            Option<Value>,
            Uuid,
            Option<Uuid>,
        ) = sqlx::query_as(
            "SELECT actor, action, object_kind, object_id, previous_state, correlation_id, bundle_id \
                 FROM history",
        )
        .fetch_one(&pool)
        .await
        .unwrap();
        assert_eq!(
            history,
            (
                principal.id().uuid(),
                "notes.create".to_owned(),
                "note".to_owned(),
                note_id,
                None,
                correlation_id,
                None,
            )
        );

        let event: (String, Value, Uuid, Uuid) =
            sqlx::query_as("SELECT event, payload, actor, correlation_id FROM outbox")
                .fetch_one(&pool)
                .await
                .unwrap();
        assert_eq!(
            event,
            (
                "note.created".to_owned(),
                json!({ "id": note_id }),
                principal.id().uuid(),
                correlation_id,
            )
        );
    }

    #[sqlx::test]
    async fn failure_after_writes_leaves_nothing_behind(pool: PgPool) {
        let (frame, principal) = setup(&pool).await;

        let error = frame
            .execute(
                &principal,
                "notes.create_then_fail",
                create_params(principal),
                Uuid::new_v4(),
                Run::Apply,
            )
            .await
            .unwrap_err();

        assert_eq!(error.code, ErrorCode::Database);
        assert_eq!(count(&pool, "example_note").await, 0);
        assert_eq!(count(&pool, "history").await, 0);
        assert_eq!(count(&pool, "outbox").await, 0);
    }

    #[sqlx::test]
    async fn failure_while_writing_history_rolls_back_the_change(pool: PgPool) {
        let (frame, _) = setup(&pool).await;
        // Ohne Zeile in `person` verletzt der Verlauf den Fremdschlüssel.
        let stranger = frame.test_actor(ActorKind::Person).await.unwrap();
        sqlx::query("DELETE FROM person WHERE id = $1")
            .bind(stranger.id().uuid())
            .execute(&pool)
            .await
            .unwrap();

        let error = frame
            .execute(
                &stranger,
                "notes.create",
                create_params(stranger),
                Uuid::new_v4(),
                Run::Apply,
            )
            .await
            .unwrap_err();

        assert_eq!(error.code, ErrorCode::Database);
        assert_eq!(count(&pool, "example_note").await, 0);
        assert_eq!(count(&pool, "outbox").await, 0);
    }

    #[sqlx::test]
    async fn dry_run_returns_the_change_list_and_writes_nothing(pool: PgPool) {
        let (frame, principal) = setup(&pool).await;

        let outcome = frame
            .execute(
                &principal,
                "notes.create",
                create_params(principal),
                Uuid::new_v4(),
                Run::DryRun,
            )
            .await
            .unwrap();

        assert!(!outcome.applied);
        assert_eq!(outcome.changes.len(), 1);
        assert_eq!(outcome.changes[0].action, "notes.create");
        assert_eq!(
            outcome.changes[0].new_state,
            Some(json!({ "text": "Hello" }))
        );
        assert_eq!(outcome.events.len(), 1);
        assert_eq!(count(&pool, "example_note").await, 0);
        assert_eq!(count(&pool, "history").await, 0);
        assert_eq!(count(&pool, "outbox").await, 0);
    }

    #[sqlx::test]
    async fn dry_run_fails_like_apply_when_the_actor_has_no_person_row(pool: PgPool) {
        let (frame, _) = setup(&pool).await;
        let stranger = frame.test_actor(ActorKind::Person).await.unwrap();
        sqlx::query("DELETE FROM person WHERE id = $1")
            .bind(stranger.id().uuid())
            .execute(&pool)
            .await
            .unwrap();

        let error = frame
            .execute(
                &stranger,
                "notes.create",
                create_params(stranger),
                Uuid::new_v4(),
                Run::DryRun,
            )
            .await
            .unwrap_err();

        assert_eq!(error.code, ErrorCode::Database);
        assert_eq!(error.params["sqlstate"], "23503");
    }

    #[sqlx::test]
    async fn out_of_scope_looks_like_a_missing_object(pool: PgPool) {
        let (frame, principal) = setup(&pool).await;
        let other = frame.test_actor(ActorKind::Person).await.unwrap();
        let foreign_note = Uuid::new_v4();
        sqlx::query("INSERT INTO example_note (id, owner, text) VALUES ($1, $2, 'secret')")
            .bind(foreign_note)
            .bind(other.id().uuid())
            .execute(&pool)
            .await
            .unwrap();

        let read = |owner: Principal, id: Uuid| {
            let frame = frame.clone();
            async move {
                frame
                    .execute(
                        &principal,
                        "notes.read",
                        json!({ "owner": owner.id(), "id": id }),
                        Uuid::new_v4(),
                        Run::Apply,
                    )
                    .await
                    .unwrap_err()
            }
        };

        let foreign_existing = read(other, foreign_note).await;
        let foreign_missing = read(other, Uuid::new_v4()).await;
        let own_missing = read(principal, Uuid::new_v4()).await;

        assert_eq!(foreign_existing.code, ErrorCode::NotFound);
        assert_eq!(foreign_existing, foreign_missing);
        assert_eq!(foreign_existing, own_missing);
    }

    #[sqlx::test]
    async fn read_operation_reads_within_scope(pool: PgPool) {
        let (frame, principal) = setup(&pool).await;
        let created = frame
            .execute(
                &principal,
                "notes.create",
                create_params(principal),
                Uuid::new_v4(),
                Run::Apply,
            )
            .await
            .unwrap();

        let read = frame
            .execute(
                &principal,
                "notes.read",
                json!({ "owner": principal.id(), "id": created.result["id"] }),
                Uuid::new_v4(),
                Run::Apply,
            )
            .await
            .unwrap();

        assert_eq!(read.result, json!({ "text": "Hello" }));
        assert!(read.changes.is_empty());
    }

    #[sqlx::test]
    async fn read_operation_cannot_write(pool: PgPool) {
        let (frame, principal) = setup(&pool).await;

        let database_write = frame
            .execute(
                &principal,
                "notes.write_while_reading",
                create_params(principal),
                Uuid::new_v4(),
                Run::Apply,
            )
            .await
            .unwrap_err();
        let recorded_change = frame
            .execute(
                &principal,
                "notes.record_while_reading",
                create_params(principal),
                Uuid::new_v4(),
                Run::Apply,
            )
            .await
            .unwrap_err();

        assert_eq!(database_write.code, ErrorCode::ReadOnly);
        assert_eq!(recorded_change.code, ErrorCode::ReadOnly);
        assert_eq!(count(&pool, "example_note").await, 0);
    }

    #[sqlx::test]
    async fn unknown_operation_and_bad_params_are_error_codes(pool: PgPool) {
        let (frame, principal) = setup(&pool).await;

        let unknown = frame
            .execute(
                &principal,
                "notes.vanish",
                json!({}),
                Uuid::new_v4(),
                Run::Apply,
            )
            .await
            .unwrap_err();
        let invalid = frame
            .execute(
                &principal,
                "notes.create",
                json!({ "owner": "not-a-uuid" }),
                Uuid::new_v4(),
                Run::Apply,
            )
            .await
            .unwrap_err();

        assert_eq!(unknown.code, ErrorCode::UnknownOperation);
        assert_eq!(unknown.params["operation"], "notes.vanish");
        assert_eq!(invalid.code, ErrorCode::InvalidParams);
        assert_eq!(invalid.params["operation"], "notes.create");
    }

    #[test]
    fn operation_names_are_unique() {
        let mut names: Vec<_> = registered_operations()
            .map(|registration| registration.name)
            .collect();
        let total = names.len();
        names.sort_unstable();
        names.dedup();
        assert_eq!(names.len(), total);
    }

    #[test]
    fn operation_schema_snapshot() {
        insta::assert_json_snapshot!(Frame::describe());
    }

    #[sqlx::test]
    async fn test_principal_is_refused_in_production(pool: PgPool) {
        let production = Frame::new(pool.clone(), Environment::Production);

        let error = production.test_principal().await.unwrap_err();

        assert_eq!(error.code, ErrorCode::TestPrincipalForbidden);
        let actor = production.test_actor(ActorKind::Guest).await.unwrap_err();
        assert_eq!(actor.code, ErrorCode::TestPrincipalForbidden);
        assert_eq!(count(&pool, "person").await, 0);
    }

    #[test]
    fn only_known_environment_names_parse() {
        assert_eq!(
            Environment::parse("production"),
            Ok(Environment::Production)
        );
        assert!(Environment::parse("prod").is_err());
        assert!(Environment::parse("").is_err());
        assert!(!Environment::Production.allows_test_principal());
    }
}
