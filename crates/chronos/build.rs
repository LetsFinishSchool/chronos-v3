// `sqlx::migrate!` bettet die Dateien beim Übersetzen ein; ohne diese Zeile übersieht
// Cargo neue Migrationen.
fn main() {
    println!("cargo:rerun-if-changed=migrations");
}
