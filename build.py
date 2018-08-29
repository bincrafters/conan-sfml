#!/usr/bin/env python
# -*- coding: utf-8 -*-


from bincrafters import build_template_default
import copy

def is_not_bad_build(build):
    if build.options['sfml:graphics'] or build.options['sfml:audio']:
        if build.settings['compiler'] == 'gcc' and build.settings['compiler.version'] == '8':
            return False
        if build.settings['compiler'] == 'clang' and build.settings['compiler.version'] == '6.0':
            return False
    return True

def add_build_requires(builds):
    return map(add_required_installers, builds)

def add_required_installers(build):
    installers = ['ninja_installer/1.8.2@bincrafters/stable']
    build.build_requires.update({"*": installers})
    return build

if __name__ == "__main__":

    builder = build_template_default.get_builder(pure_c=False)

    for build in builder.items:
        build.options['sfml:window'] = False
        build.options['sfml:graphics'] = False
        build.options['sfml:audio'] = False
        build.options['sfml:network'] = False

    builds = list(builder.items)
    for option in ['sfml:window', 'sfml:graphics', 'sfml:audio', 'sfml:network']:
        new_builds = copy.deepcopy(builds)
        for build in new_builds:
            build.options[option] = True
        builder.items.extend(new_builds)
    
    builder.items = add_build_requires(builder.items)
    
    # Some dependencies don't have gcc-8 or clang-6.0 binaries, so some SFML libs fail to build
    builder.builds = filter(is_not_bad_build, builder.items)

builder.run()