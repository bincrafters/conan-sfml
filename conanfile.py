#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os, shutil


class SfmlConan(ConanFile):
    name = 'sfml'
    version = '2.5.0'
    description = 'Simple and Fast Multimedia Library'
    url = 'https://github.com/bincrafters/conan-sfml'
    homepage = 'https://github.com/SFML/SFML'
    author = 'Bincrafters <bincrafters@gmail.com>'
    license = 'zlib/png'

    exports = ['LICENSE.md']

    exports_sources = ['CMakeLists.txt']
    generators = 'cmake'

    settings = 'os', 'compiler', 'build_type', 'arch'
    options = {
        'shared': [True, False],
        'fPIC': [True, False],
        'window': [True, False],
        'graphics': [True, False],
        'network': [True, False],
        'audio': [True, False],
    }
    default_options = 'shared=False', 'fPIC=True', 'window=False', 'graphics=False', 'network=False', 'audio=False'

    source_subfolder = 'source_subfolder'
    build_subfolder = 'build_subfolder'

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def configure(self):
        if self.options.graphics:
            self.options.window = True

    def requirements(self):
        if self.options.graphics:
            self.requires.add('freetype/2.9.0@bincrafters/stable')
            self.requires.add('stb/20180214@conan/stable')
        if self.options.audio:
            self.requires.add('openal/1.18.2@bincrafters/stable')
            self.requires.add('flac/1.3.2@bincrafters/stable')
            self.requires.add('ogg/1.3.3@bincrafters/stable')
            self.requires.add('vorbis/1.3.6@bincrafters/stable')

    def system_requirements(self):
        if self.settings.os == 'Linux' and tools.os_info.is_linux:
            if tools.os_info.with_apt:
                installer = tools.SystemPackageTool()
                if self.settings.arch == 'x86':
                    arch_suffix = ':i386'
                elif self.settings.arch == 'x86_64':
                    arch_suffix = ':amd64'

                packages = ['pkg-config%s' % arch_suffix]

                if self.options.window:
                    packages.extend(['libx11-dev%s' % arch_suffix])
                    packages.extend(['libxrandr-dev%s' % arch_suffix])
                    packages.extend(['libudev-dev%s' % arch_suffix])
                    packages.extend(['libgl1-mesa-dev%s' % arch_suffix])

                for package in packages:
                    installer.install(package)

    def source(self):
        tools.get('{0}/archive/{1}.tar.gz'.format(self.homepage, self.version))
        extracted_dir = 'SFML-' + self.version
        os.rename(extracted_dir, self.source_subfolder)
        tools.replace_in_file(self.source_subfolder + '/cmake/Modules/FindFLAC.cmake',
                            'find_library(FLAC_LIBRARY NAMES FLAC)',
                            'find_library(FLAC_LIBRARY NAMES flac)')
        tools.replace_in_file(self.source_subfolder + '/cmake/Modules/FindFreetype.cmake', 'libfreetype', 'libfreetype\n    freetyped')
        tools.replace_in_file(self.source_subfolder + '/src/SFML/Graphics/CMakeLists.txt', 'PRIVATE Freetype', 'PRIVATE ${CONAN_LIBS}')
        if self.settings.os == 'Macos':
            tools.replace_in_file(self.source_subfolder + '/src/SFML/Audio/CMakeLists.txt', 'PRIVATE OpenAL', 'PRIVATE ${CONAN_LIBS} "-framework AudioUnit"')
        else:
            tools.replace_in_file(self.source_subfolder + '/src/SFML/Audio/CMakeLists.txt', 'PRIVATE OpenAL', 'PRIVATE ${CONAN_LIBS}')
        shutil.rmtree(os.path.join(self.source_subfolder, 'extlibs'))

    def configure_cmake(self):
        cmake = CMake(self, generator='Ninja')
        cmake.definitions['SFML_DEPENDENCIES_INSTALL_PREFIX'] = self.package_folder
        cmake.definitions['SFML_MISC_INSTALL_PREFIX'] = self.package_folder

        cmake.definitions['SFML_BUILD_WINDOW'] = self.options.window
        cmake.definitions['SFML_BUILD_GRAPHICS'] = self.options.graphics
        cmake.definitions['SFML_BUILD_NETWORK'] = self.options.network
        cmake.definitions['SFML_BUILD_AUDIO'] = self.options.audio

        if self.settings.os == 'Windows':
            if self.settings.compiler.runtime == 'MT' or self.settings.compiler.runtime == 'MTd':
                cmake.definitions['SFML_USE_STATIC_STD_LIBS'] = True

        if self.settings.os != 'Windows':
            cmake.definitions['CMAKE_POSITION_INDEPENDENT_CODE'] = self.options.fPIC
        cmake.configure(build_folder=self.build_subfolder)
        return cmake

    def build(self):
        if self.settings.compiler == 'Visual Studio':
            with tools.vcvars(self.settings, force=True, filter_known_paths=False):
                cmake = self.configure_cmake()
        else:
            cmake = self.configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern='License.md', dst='licenses', src=self.source_subfolder)
        include_folder = os.path.join(self.source_subfolder, "include")
        self.copy(pattern="*", dst="include", src=include_folder)
        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", keep_path=False)

        if self.settings.os == 'Macos' and self.options.shared and self.options.graphics:
            with tools.chdir(os.path.join(self.package_folder, 'lib')):
                suffix = '-d' if self.settings.build_type == 'Debug' else ''
                graphics_library = 'libsfml-graphics%s.%s.dylib' % (suffix, self.version)
                old_path = '@rpath/../Frameworks/freetype.framework/Versions/A/freetype'
                new_path = '@loader_path/../freetype.framework/Versions/A/freetype'
                command = 'install_name_tool -change %s %s %s' % (old_path, new_path, graphics_library)
                self.output.warn(command)
                self.run(command)

    def add_libraries_from_pc(self, library, static=None):
        if static is None:
            static = not self.options.shared
        pkg_config = tools.PkgConfig(library, static=static)
        libs = [lib[2:] for lib in pkg_config.libs_only_l]  # cut -l prefix
        lib_paths = [lib[2:] for lib in pkg_config.libs_only_L]  # cut -L prefix
        self.cpp_info.libs.extend(libs)
        self.cpp_info.libdirs.extend(lib_paths)
        self.cpp_info.sharedlinkflags.extend(pkg_config.libs_only_other)
        self.cpp_info.exelinkflags.extend(pkg_config.libs_only_other)

    def package_info(self):
        self.cpp_info.defines = ['SFML_STATIC'] if not self.options.shared else []

        suffix = '-s' if not self.options.shared else ''
        suffix += '-d' if self.settings.build_type == 'Debug' else ''
        sfml_main_suffix = '-d' if self.settings.build_type == 'Debug' else ''

        if self.options.graphics:
            self.cpp_info.libs.append('sfml-graphics' + suffix)
        if self.options.window:
            self.cpp_info.libs.append('sfml-window' + suffix)
        if self.options.network:
            self.cpp_info.libs.append('sfml-network' + suffix)
        if self.options.audio:
            self.cpp_info.libs.append('sfml-audio' + suffix)
        if self.settings.os == 'Windows':
            self.cpp_info.libs.append('sfml-main' + sfml_main_suffix)
        self.cpp_info.libs.append('sfml-system' + suffix)

        if not self.options.shared:
            if self.settings.os == 'Windows':
                if self.options.graphics:
                    self.cpp_info.libs.append('freetype')
                if self.options.window:
                    self.cpp_info.libs.append('opengl32')
                    self.cpp_info.libs.append('gdi32')
                if self.options.audio:
                    self.cpp_info.libs.append('openal32')
                    self.cpp_info.libs.append('flac')
                    self.cpp_info.libs.append('vorbisenc')
                    self.cpp_info.libs.append('vorbisfile')
                    self.cpp_info.libs.append('vorbis')
                    self.cpp_info.libs.append('ogg')
                if self.options.network:
                    self.cpp_info.libs.append('ws2_32')
                self.cpp_info.libs.append('winmm')
            elif self.settings.os == 'Linux':
                if self.options.window:
                    self.add_libraries_from_pc('xrandr')
                if self.options.graphics:
                    self.cpp_info.libs.append('GL')
                    self.cpp_info.libs.append('udev')
            elif self.settings.os == "Macos":
                frameworks = []
                if self.options.window:
                    frameworks.extend(['Cocoa', 'IOKit', 'Carbon', 'OpenGL'])
                for framework in frameworks:
                    self.cpp_info.exelinkflags.append("-framework %s" % framework)
                self.cpp_info.sharedlinkflags = self.cpp_info.exelinkflags
