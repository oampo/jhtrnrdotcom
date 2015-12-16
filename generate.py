"""
Usage:
  generate.py <indir> <outdir>

Options:
  -h --help     Show this screen.
"""

import os
import os.path
import shutil
import sys
import re
import errno

from docopt import docopt
import frontmatter
import yaml
from jinja2 import Template, FileSystemLoader, Environment, Undefined
from bs4 import BeautifulSoup


TEMPLATE_DIR = "templates"
DEFAULT_TEMPLATE = "page.html"
TEMPLATE_PATTERN = r"^.*\.html$"
PAGES_PATTERN = r"^.*/index.html?$"
IGNORE_PATTERNS = [r"^.*\.swp$"]
ASSET_DIR = "public"
INDEX_PATTERNS = [r"^(.*/)index.html?$"]

class SilentUndefined(Undefined):
    def _fail_with_undefined_error(self, *args, **kwargs):
        return ''

def paths(directory, ignore_patterns):
    for root, subdirs, files in os.walk(directory, followlinks=True):
        for file in files:
            path_with_base = os.path.join(root, file)
            path = os.path.relpath(path_with_base, directory)

            for pattern in ignore_patterns:
                if re.match(pattern, path):
                    break
            else:
                yield path, {"path": path, "path_with_base": path_with_base}

def urls(files, index_patterns):
    for path, file in files:
        full_url = url = "/" + path
        for pattern in index_patterns:
            match = re.match(pattern, full_url)
            if match:
                url = match.group(1)
                break
        file["url"] = url
        file["full_url"] = full_url
        yield path, file

def read(files, metadata):
    for path, file in files:
        try:
            with open(file["path_with_base"]) as f:
                file["contents"] = f.read()
                file["is_binary"] = False
                yield path, file
        except UnicodeDecodeError:
            file["is_binary"] = True
            yield path, file

def parse_frontmatter(files, metadata):
    for path, file in files:
        if file["is_binary"]:
            yield path, file
            continue
        file_metadata, contents = frontmatter.parse(file["contents"])
        file.update(file_metadata)
        file["contents"] = contents.strip()
        yield path, file

def yaml_frontmatter(files, metadata):
    files = dict(files)
    for path, file in files.items():
        _, extension = os.path.splitext(path)
        if extension == ".yml" or extension == ".yaml":
            data = yaml.load(file["contents"])
            if "for" in data:
                target = data["for"]
                del data["for"]
                target = os.path.join(os.path.split(path)[0], target)
                files[target].update(data)
        yield path, file

def collection(files, metadata, name, pattern):
    if not "collections" in metadata:
        collections = metadata["collections"] = {}
    collection = collections[name] = []
    for path, file in files:
        if re.match(pattern, path):
            collection.append(file)
            file["collection"] = name
        yield path, file

def sort_collections(files, metadata):
    files = dict(files)
    if not "collections" in metadata:
        return files

    collections = metadata["collections"]
    for name, collection in collections.items():
        collection.sort(key=lambda file: file["title"].lower())
        for index, file in enumerate(collection):
            file[name + "_index"] = index
    return files

def collection_links(files, metadata):
    files = dict(files)
    for path, file in files.items():
        if "collection" in file:
            name = file["collection"]
            collection = metadata["collections"][name]
            index = file[name + "_index"]
            if index > 0:
                file["previous"] = collection[index - 1]
            if index < len(collection) - 1:
                file["next"] = collection[index + 1]
        yield path, file

def template(files, metadata, pattern, default, directory):
    jinja = Environment(loader=FileSystemLoader(directory),
                        undefined=SilentUndefined, trim_blocks=True,
                        lstrip_blocks=True)

    for path, file in files:
        if re.match(pattern, path):
            if "template" not in file:
                file["template"] = default
            template = jinja.get_template(file["template"])
            file["contents"] = template.render(dict(file, **metadata))
        yield path, file

def prettify(files, metadata):
    for path, file in files:
        _, extension = os.path.splitext(path)
        if extension == ".html":
            soup = BeautifulSoup(file["contents"], "html5lib")
            contents = soup.prettify()
            contents = re.sub(r"^( +)", r"\1\1\1\1", contents,
                              flags=re.MULTILINE)
            file["contents"] = contents
        yield path, file

def write(files, metadata, directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)

    for path, file in files:
        output_path = os.path.join(directory, path)
        output_directory = os.path.dirname(output_path)
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        if file["is_binary"]:
            shutil.copy(file["path_with_base"], output_path)
        else:
            with open(output_path, "w") as f:
                f.write(file["contents"])


def assets(source, destination):
    for path in os.listdir(source):
        source_path = os.path.join(source, path)
        destination_path = os.path.join(destination, path)
        if os.path.isdir(source_path):
            shutil.copytree(source_path, destination_path)
        elif os.path.isfile(source_path):
            shutil.copy(source_path, destination_path)

if __name__ == "__main__":
    arguments = docopt(__doc__)
    indir = arguments["<indir>"]
    outdir = arguments["<outdir>"]

    jinja = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

    metadata = {
        "site": {
            "url": "https://www.jhtrnr.com",
            "title": "Joe Turner"
        }
    }
    files = paths(indir, IGNORE_PATTERNS)
    files = urls(files, INDEX_PATTERNS)
    files = read(files, metadata)
    files = parse_frontmatter(files, metadata)
    files = yaml_frontmatter(files, metadata)
    files = collection(files, metadata, "pages", PAGES_PATTERN)
    files = sort_collections(files, metadata)
    files = collection_links(files, metadata)
    files = template(files, metadata, TEMPLATE_PATTERN, DEFAULT_TEMPLATE, TEMPLATE_DIR)
    files = prettify(files, metadata)
    write(files, metadata, outdir)
    assets(ASSET_DIR, outdir)

