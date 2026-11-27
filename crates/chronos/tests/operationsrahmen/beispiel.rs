//! Beispieloperationen für die Tests des Rahmens. Sie sind kein Fachcode und belegen den
//! ganzen Weg: Fachänderung, Verlauf und Outbox-Ereignis in einer Transaktion.

use chronos_core::schema::JsonSchema;
use chronos_core::{
    Change, Context, Error, ErrorCode, Event, Mode, Operation, PersonId, Scope, register_operation,
};
use serde::{Deserialize, Serialize};
use serde_json::json;
use uuid::Uuid;

pub const SETUP_SQL: &str = "CREATE TABLE example_note (
    id uuid PRIMARY KEY,
    owner uuid NOT NULL,
    text text NOT NULL
)";

#[derive(Deserialize, JsonSchema)]
#[schemars(crate = "chronos_core::schema::schemars")]
pub struct CreateNote {
    pub owner: PersonId,
    pub text: String,
}

#[derive(Serialize, JsonSchema)]
#[schemars(crate = "chronos_core::schema::schemars")]
pub struct NoteCreated {
    pub id: Uuid,
}

async fn insert_note(ctx: &mut Context<'_>, owner: PersonId, text: &str) -> Result<Uuid, Error> {
    let id = Uuid::new_v4();
    sqlx::query("INSERT INTO example_note (id, owner, text) VALUES ($1, $2, $3)")
        .bind(id)
        .bind(owner.uuid())
        .bind(text)
        .execute(ctx.db())
        .await?;
    Ok(id)
}

fn note_created(id: Uuid, text: &str) -> Change {
    Change {
        action: "notes.create".to_owned(),
        object_kind: "note".to_owned(),
        object_id: id,
        before: None,
        after: Some(json!({ "text": text })),
    }
}

pub struct NotesCreate;

impl Operation for NotesCreate {
    type Params = CreateNote;
    type Output = NoteCreated;
    const NAME: &'static str = "notes.create";
    const DESCRIPTION: &'static str = "Creates a note owned by the given person.";
    const MODE: Mode = Mode::Write;

    fn scope(params: &CreateNote) -> Scope {
        Scope::Person(params.owner)
    }

    async fn run(ctx: &mut Context<'_>, params: CreateNote) -> Result<NoteCreated, Error> {
        let id = insert_note(ctx, params.owner, &params.text).await?;
        ctx.record_change(note_created(id, &params.text))?;
        ctx.emit(Event {
            name: "note.created".to_owned(),
            payload: json!({ "id": id }),
        })?;
        Ok(NoteCreated { id })
    }
}
register_operation!(NotesCreate);

/// Schreibt, meldet Änderung und Ereignis und scheitert dann.
pub struct NotesCreateThenFail;

impl Operation for NotesCreateThenFail {
    type Params = CreateNote;
    type Output = NoteCreated;
    const NAME: &'static str = "notes.create_then_fail";
    const DESCRIPTION: &'static str = "Creates a note and then fails; leaves nothing behind.";
    const MODE: Mode = Mode::Write;

    fn scope(params: &CreateNote) -> Scope {
        Scope::Person(params.owner)
    }

    async fn run(ctx: &mut Context<'_>, params: CreateNote) -> Result<NoteCreated, Error> {
        let id = insert_note(ctx, params.owner, &params.text).await?;
        ctx.record_change(note_created(id, &params.text))?;
        ctx.emit(Event {
            name: "note.created".to_owned(),
            payload: json!({ "id": id }),
        })?;
        Err(Error::new(ErrorCode::Database).with("reason", "test"))
    }
}
register_operation!(NotesCreateThenFail);

#[derive(Deserialize, JsonSchema)]
#[schemars(crate = "chronos_core::schema::schemars")]
pub struct ReadNote {
    pub owner: PersonId,
    pub id: Uuid,
}

#[derive(Serialize, JsonSchema)]
#[schemars(crate = "chronos_core::schema::schemars")]
pub struct Note {
    pub text: String,
}

pub struct NotesRead;

impl Operation for NotesRead {
    type Params = ReadNote;
    type Output = Note;
    const NAME: &'static str = "notes.read";
    const DESCRIPTION: &'static str = "Reads a note of the given person.";
    const MODE: Mode = Mode::Read;

    fn scope(params: &ReadNote) -> Scope {
        Scope::Person(params.owner)
    }

    async fn run(ctx: &mut Context<'_>, params: ReadNote) -> Result<Note, Error> {
        let text: Option<String> =
            sqlx::query_scalar("SELECT text FROM example_note WHERE id = $1 AND owner = $2")
                .bind(params.id)
                .bind(params.owner.uuid())
                .fetch_optional(ctx.db())
                .await?;
        text.map(|text| Note { text }).ok_or_else(Error::not_found)
    }
}
register_operation!(NotesRead);

/// Eine lesende Operation, die trotzdem schreiben will; PostgreSQL muss das ablehnen.
pub struct NotesWriteWhileReading;

impl Operation for NotesWriteWhileReading {
    type Params = CreateNote;
    type Output = NoteCreated;
    const NAME: &'static str = "notes.write_while_reading";
    const DESCRIPTION: &'static str = "A read operation that tries to write.";
    const MODE: Mode = Mode::Read;

    fn scope(params: &CreateNote) -> Scope {
        Scope::Person(params.owner)
    }

    async fn run(ctx: &mut Context<'_>, params: CreateNote) -> Result<NoteCreated, Error> {
        let id = insert_note(ctx, params.owner, &params.text).await?;
        Ok(NoteCreated { id })
    }
}
register_operation!(NotesWriteWhileReading);

/// Eine lesende Operation, die eine Änderung melden will; der Kontext lehnt das ab.
pub struct NotesRecordWhileReading;

impl Operation for NotesRecordWhileReading {
    type Params = CreateNote;
    type Output = NoteCreated;
    const NAME: &'static str = "notes.record_while_reading";
    const DESCRIPTION: &'static str = "A read operation that tries to record a change.";
    const MODE: Mode = Mode::Read;

    fn scope(params: &CreateNote) -> Scope {
        Scope::Person(params.owner)
    }

    async fn run(ctx: &mut Context<'_>, params: CreateNote) -> Result<NoteCreated, Error> {
        let id = Uuid::new_v4();
        ctx.record_change(note_created(id, &params.text))?;
        Ok(NoteCreated { id })
    }
}
register_operation!(NotesRecordWhileReading);
