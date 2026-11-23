use zed_extension_api as zed;

struct Pooka;

impl zed::Extension for Pooka {
    fn new() -> Self {
        Self
    }

    fn language_server_command(
        &mut self,
        server: &zed::LanguageServerId,
        worktree: &zed::Worktree,
    ) -> zed::Result<zed::Command> {
        let configured = zed::settings::LspSettings::for_worktree(server.as_ref(), worktree)
            .ok()
            .and_then(|settings| settings.binary)
            .and_then(|binary| binary.path);
        let command = configured
            .or_else(|| worktree.which("pooka"))
            .ok_or_else(|| "Install Pooka or configure the pooka language server binary".to_string())?;
        Ok(zed::Command {
            command,
            args: vec!["lsp".into()],
            env: Default::default(),
        })
    }
}

zed::register_extension!(Pooka);
