#!/usr/bin/env python
# -*- coding: utf-8 -*-


from bincrafters import build_template_default
import copy

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
    
builder.run()
