from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from marko import Markdown, block, inline
from marko.helpers import MarkoExtension
from marko.element import Element
import shutil
import re
from urllib.parse import unquote

from jinja2 import Environment, FileSystemLoader

ALL_POSTS_NAME = "All Posts" # set to None to get rid of the all notes page
FRONT_MATTER_TITLE = "title"
FRONT_MATTER_DATE = "date"

DATE_FORMATS = [
    "%Y-%m-%d",
    "%y-%m-%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%d/%m/%Y",
    "%d/%m/%Y",
]  # assume US format first


@dataclass
class Link:
    href: str
    text: str
    prefix: str = None
    suffix: str = None


def _get_date(date_str_or_tstamp):
    try:
        date = datetime.fromtimestamp(date_str_or_tstamp)
        return date
    except TypeError:
        pass

    for fmt in DATE_FORMATS:
        try:
            date = datetime.strptime(date_str_or_tstamp, fmt)
            return date
        except ValueError:
            pass

    raise ValueError(f"Could not parse date: {date_str_or_tstamp}")

## Parse latex and render for MathJax
class LatexElement(inline.InlineElement):
    def __init__(self, match):
        self.children = match.group(1)
        return

    @classmethod
    def find(cls, text: str, *, source):
        """This method should return an iterable containing matches of this element."""
        return cls.pattern.finditer(text)


class BlockLatex(LatexElement):
    pattern = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)

    def __init__(self, match):
        self.children = match.group(1)
        return


class InlineLatex(LatexElement):
    pattern = re.compile(r"\$(.*?)\$")

    def __init__(self, match):
        self.children = match.group(1)
        return


class BlockLatexRenderMixin:
    def render_block_latex(self, element: inline.InlineElement):
        return f'<div class="block-latex">\[{element.children}\]</div>'


class InlineLatexRenderMixin:
    def render_inline_latex(self, element: inline.InlineElement):
        return f'<span class="inline-latex">\({element.children}\)</div>'


BlockLatexExtension = MarkoExtension(
    elements=[BlockLatex, InlineLatex],
    renderer_mixins=[BlockLatexRenderMixin, InlineLatexRenderMixin],
)


def normalize_link(link: str, from_root=False) -> str:
    p = Path(link)
    stem = p.stem
    uri = str(p.with_stem(stem).with_suffix(".html"))
    if from_root:
        return f"/{uri}"
    return uri


def filter_doc(doc: block.Document) -> block.Document:
    """ get rid of front matter and other stuff"""
    import copy

    new_doc = copy.deepcopy(doc)
    new_ch = []
    for ch in doc.children:
        if isinstance(ch, (block.SetextHeading, block.BlankLine, block.ThematicBreak)):
            continue
        new_ch.append(ch)

    new_doc.children = new_ch
    return new_doc


class NodeVisitor:
    def __init__(self):
        self.depth = -1
        self.cnt = 0
        return

    def visit(self, node):
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        self.cnt += 1
        self.depth += 1
        ind = "\t" * self.depth
        print(f"{ind}{self.cnt}: {node.__class__.__name__}")
        if isinstance(node, Element):
            if isinstance(node.children, list):
                for ch in node.children:
                    self.visit(ch)
            elif isinstance(node.children, Element):
                self.visit(node.children)
        self.depth -= 1
        return


class NoteProcessor(NodeVisitor):
    def __init__(self, path: str):
        super().__init__()
        self.path = Path(path)
        self.doc = Markdown(extensions=[BlockLatexExtension]).parse(
            self.path.read_text()
        )
        self.cnt = 0
        self.out_links = {}
        self.backlinks = []
        self.statics_to_copy = []
        self.header = {}
        self.visit(self.doc)
        self.note_date = _get_date(self.header.get(FRONT_MATTER_DATE, self.path.stat().st_ctime))
        return

    def add_backlink(self, from_uri, text):
        self.backlinks.append(Link(href=from_uri, text=text))
        return

    def visit_SetextHeading(self, node):
        self._is_heading = True
        for ch in node.children:
            if isinstance(ch, inline.RawText):
                k, *vals = ch.children.split(":")
                v = ":".join(vals)
                self.header[k.strip()] = v.strip().replace('"', "")
        self.generic_visit(node)
        self._is_heading = False
        return

    def visit_Image(self, node):
        if not node.dest.startswith("http"):
            img = self.path.parent / unquote(node.dest)
            if img.exists():
                self.statics_to_copy.append(img)
        return

    def visit_Link(self, node):
        if node.dest.startswith("http"):
            self.out_links[node.dest] = Link(href=node.dest, text=node.children[0].children)
            return

        if node.dest.endswith(".md"):
            # self.out_links.add(node.dest)
            uri = normalize_link(node.dest, from_root=True)
            self.out_links[unquote(node.dest)] = Link(href=uri, text=node.children[0].children)
            node.dest = uri
        else:
            pass

        self.generic_visit(node)
        return


if __name__ == "__main__":
    env = Environment(loader=FileSystemLoader("templates"))
    # Load the template from file
    note_template = env.get_template("note.html")
    root = Path("notes/.")
    out = Path("output")
    out.mkdir(exist_ok=True)

    shutil.copytree("static", "output/static", dirs_exist_ok=True)

    get_all_docs = lambda: (fp for fp in root.glob("**/*.md") if fp.is_file())
    all_docs = {
        str(fp.relative_to(root)): NoteProcessor(str(fp)) for fp in get_all_docs()
    }
    for fp in get_all_docs():
        doc = all_docs[str(fp.relative_to(root))]
        for fname, link in doc.out_links.items():
            if fname in all_docs:
                uri = normalize_link(doc.path.relative_to(root), from_root=True)
                all_docs[fname].add_backlink(
                    from_uri=uri, text=doc.header.get("title", doc.path.stem)
                )

    for doc in all_docs.values():
        for static in doc.statics_to_copy:
            new_static = out / static.relative_to(root)
            new_static.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy(static, new_static)

    _is_top_level = lambda p: len(Path(p).parts) == 1
    top_level = [
        Link(
            href=normalize_link(v.path.relative_to(root), from_root=True),
            text=v.path.stem.capitalize(),
        )
        for k, v in all_docs.items()
        if _is_top_level(k)
    ]
    doc_list_new_to_old = sorted(list(all_docs.items()), key=lambda x: x[1].note_date, reverse=True)

    if ALL_POSTS_NAME is not None:
        top_level.append(Link(
            href=normalize_link(ALL_POSTS_NAME, from_root=True),
            text=ALL_POSTS_NAME,
        ))

    all_posts_list = []
    for k, doc_obj in doc_list_new_to_old:
        html = out / Path(normalize_link(doc_obj.path.relative_to(root)))
        input_content = Markdown(extensions=[BlockLatexExtension]).render(
            filter_doc(doc_obj.doc)
        )
        note_title = doc_obj.header.get(FRONT_MATTER_TITLE, doc_obj.path.stem) 

        rendered_html = note_template.render(
            header=note_title,
            content=input_content,
            backlinks=doc_obj.backlinks,
            # refs=list(doc_obj.out_links.values()),
            header_menu=top_level,
            disqus=doc_obj.header.get("disqus", None),
        )
        html.parent.mkdir(exist_ok=True, parents=True)
        html.write_text(rendered_html)

        if ALL_POSTS_NAME is not None and not _is_top_level(doc_obj.path.relative_to(root)):
            all_posts_list.append(Link(
                href=normalize_link(html.relative_to(out)),
                text=note_title,
                prefix=doc_obj.note_date.strftime("%Y-%m-%d"),
            ))
        for fp in doc_obj.statics_to_copy:
            new_static = out / fp.resolve().relative_to(Path(__file__).parent)
            new_static.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy(fp, new_static)
    
    if all_posts_list:
        all_posts_html = (out / ALL_POSTS_NAME).with_suffix(".html")
        all_posts_temp = env.get_template("list.html")
        rendered_html = all_posts_temp.render(
            posts=all_posts_list,
            header_menu=top_level,
            header=ALL_POSTS_NAME,
        )
        all_posts_html.write_text(rendered_html)

    pass
