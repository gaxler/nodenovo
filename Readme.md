🚀 Welcome to the Obsidian to GitHub Hacky Minimalist Converter!

Ever dreamt of turning your Obsidian notes into a minimalist GitHub Pages website? No hah?  Well this thing is here anyways:

- Fork this repo
- There's an Obsidian vault under `notes` folder here. You can adapt it as your own and push
- A github action and a hacky `build.py` script will turn the vault into a GithubPages website for the notes
- It supports latex, code highlighting and images and appends backlinks to the end of the page 
### Usage comments
- All top level pages under `notes` will get turned into nav-bar items, so maybe set default subfolder for the notes.
- you also need to make sure that Obsidian keeps links in markdown format and absolute path in vault(this is already set in the default vault)
- **Never tested but probably works with other markdown editors** Script only assumes markdown files and dollar sign for inline latex and double dollar sign for block latex.
- **Disqus** - you can add a Disqus threads to notes by specifying frontmatter fields `disqus` and set fields value to the name of your disqus site
