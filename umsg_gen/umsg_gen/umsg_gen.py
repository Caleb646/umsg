from jinja2 import Environment, FileSystemLoader
import json
import glob
import argparse
import shutil
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', dest='msgs_directory', required=True)
    parser.add_argument('-o', dest='output_directory', required=True)
    parser.add_argument('--with-core', dest='with_core', action='store_true',
                        help='also copy the umsg core (inc/, src/) into <output>/core. '
                             'The copy in this package is the source of truth; use this '
                             'to refresh a checked-in copy such as umsg_lib/core instead '
                             'of hand-editing both and letting them drift.')
    args = parser.parse_args()

    # create full paths
    msg_def_path = Path().resolve() / args.msgs_directory
    output_path = Path().resolve() / args.output_directory
    templates_path = Path(__file__).resolve().parent / 'templates'
    core_path = Path(__file__).resolve().parent / 'core'

    # Off by default: consumers that already compile the core from elsewhere
    # (Flapjack builds it straight out of umsg_lib/core) would otherwise get an
    # unused second copy dropped into their generated message directory.
    if args.with_core:
        shutil.copytree(core_path, output_path / 'core', dirs_exist_ok=True)
        print(f'copied core -> {output_path / "core"}')

    # setup jinja2 environment & templates
    env = Environment(loader=FileSystemLoader(templates_path))
    env.trim_blocks = True
    env.lstrip_blocks = True
    inc_template = env.get_template(name='msg.h.j2')
    src_template = env.get_template(name='msg.c.j2')
    cmake_template = env.get_template(name='CMakeLists.txt.j2')

    # find all topic json files
    files = glob.glob(f'{msg_def_path}/*.json')

    # if files list is empty return error
    if not files:
        print('No files found')
        exit(1)

    # generate source and header files for each topic json file
    sources = []
    for file in files:
        # load topic json file
        f = open(file)
        topic_dict = json.load(f)

        # add name field to topic dict
        topic_dict['name'] = Path(file).stem

        # generate header
        filename = f'{output_path}/umsg_{topic_dict["name"]}.h'
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        content = inc_template.render(topic_dict=topic_dict)
        with open(filename, mode="w", encoding="utf-8") as message:
            message.write(content)

        #generate source
        filename = f'{output_path}/{topic_dict["name"]}.c'
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        content = src_template.render(topic_dict=topic_dict)
        with open(filename, mode="w", encoding="utf-8") as message:
            message.write(content)

        # add file name to list
        sources.append(Path(filename).name)

if __name__ == "__main__":
    main()
