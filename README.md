# Pooka for Zed

A little Pooka in Zed: syntax highlighting, bracket matching, indentation, document outlines and file icons for `.pooka` and `.spec.pooka` files.

## Install locally

Open Zed's Extensions panel, choose **Install Dev Extension**, and select this directory. Zed builds the grammar from the revision in `extension.toml`. This package does not need any sibling checkout.

For a staged build, install Python 3.11+, Git, the Tree-sitter CLI and a WASI SDK, then run:

```sh
python3 build.py
```

Set `WASI_SDK_PATH` to your SDK directory. The builder can also use Zed's installed SDK. It fetches its own pinned grammar into `.build/`, validates the queries and writes `dist/`. Select this directory for development installation. The staged `dist/` also contains the complete extension.

## File icons

Select **Pooka** or **Pooka Light** with Zed's icon theme selector. These themes add the Pooka mark and retain the standard filename associations. `pooka.toml` keeps Zed's TOML highlighting and icon. The dark mark uses `#BCAC8F`; the light mark uses `#3B3B3B`.

## Development

Edit `languages/pooka/*.scm` directly. Configuration, queries and icons belong to this package. Grammar changes happen in [tree-sitter-pooka](https://github.com/pooka-lang/tree-sitter-pooka); update the pinned revision deliberately.

```sh
python3 build.py --check
```

This checks the sample, every query, configuration and icon files without requiring a WASI SDK. CI runs the same command.

Highlighting only: this extension does not start a compiler or language server.

## Licence

Apache-2.0. See [LICENSE](LICENSE).
