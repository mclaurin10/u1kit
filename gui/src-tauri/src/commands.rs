//! Custom Tauri commands invoked from the React side.
//!
//! Only one command today: `copy_file`, used by the Save-as flow (G8)
//! to copy the fix command's output (currently written to a derived
//! path next to the input) to a user-chosen destination.

use std::fs;
use std::path::Path;

/// Copy `src` to `dst`. Returns an error string the React side can show.
/// Overwrites an existing file at `dst` — consistent with how Save-As
/// dialogs on every major OS present the confirm-overwrite prompt
/// before this command fires.
#[tauri::command]
pub fn copy_file(src: String, dst: String) -> Result<(), String> {
    let src_path = Path::new(&src);
    let dst_path = Path::new(&dst);
    fs::copy(src_path, dst_path).map_err(|e| format!("copy failed: {e}"))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn copy_file_copies_bytes() {
        let dir = tempfile::tempdir().expect("mkdir");
        let src = dir.path().join("src.txt");
        let dst = dir.path().join("dst.txt");
        let mut f = fs::File::create(&src).expect("create src");
        f.write_all(b"hello u1kit").expect("write");

        copy_file(
            src.to_string_lossy().into_owned(),
            dst.to_string_lossy().into_owned(),
        )
        .expect("copy_file");

        let contents = fs::read_to_string(&dst).expect("read dst");
        assert_eq!(contents, "hello u1kit");
    }
}
