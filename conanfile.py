from conans import ConanFile, CMake, tools
import os


class SfmlConan(ConanFile):
    name = 'sfml'
    version = '2.5.1'
    description = 'Simple and Fast Multimedia Library'
    topics = ('conan', 'sfml', 'multimedia')
    url = 'https://github.com/bincrafters/conan-sfml'
    homepage = 'https://github.com/SFML/SFML'
    license = "ZLIB"
    exports = ['LICENSE.md']
    exports_sources = ['CMakeLists.txt', '0001-find-libraries.patch']
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
    default_options = {
        'shared': False,
        'fPIC': True,
        'window': False,
        'graphics': False,
        'network': False,
        'audio': False
    }
    _source_subfolder = 'source_subfolder'
    _build_subfolder = 'build_subfolder'

    def config_options(self):
        if self.settings.os == 'Windows':
            self.options.remove('fPIC')

    def configure(self):
        if self.options.graphics:
            self.options.window = True

    def requirements(self):
        if self.options.graphics:
            self.requires.add('freetype/2.10.1')
            self.requires.add('stb/20180214@conan/stable')
        if self.options.audio:
            self.requires.add('openal/1.19.1')
            self.requires.add('flac/1.3.2@bincrafters/stable')
            self.requires.add('ogg/1.3.4')
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
        sha256 = "438c91a917cc8aa19e82c6f59f8714da353c488584a007d401efac8368e1c785"
        tools.get('{0}/archive/{1}.tar.gz'.format(self.homepage, self.version), sha256=sha256)
        extracted_dir = 'SFML-' + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['SFML_DEPENDENCIES_INSTALL_PREFIX'] = self.package_folder
        cmake.definitions['SFML_MISC_INSTALL_PREFIX'] = self.package_folder
        cmake.definitions['SFML_BUILD_WINDOW'] = self.options.window
        cmake.definitions['SFML_BUILD_GRAPHICS'] = self.options.graphics
        cmake.definitions['SFML_BUILD_NETWORK'] = self.options.network
        cmake.definitions['SFML_BUILD_AUDIO'] = self.options.audio
        if self.settings.os == "Macos":
            cmake.definitions['SFML_OSX_FRAMEWORK'] = "-framework AudioUnit"
        elif self.settings.compiler == 'Visual Studio':
            if self.settings.compiler.runtime == 'MT' or self.settings.compiler.runtime == 'MTd':
                cmake.definitions['SFML_USE_STATIC_STD_LIBS'] = True

        extlibs_folder = os.path.join(self._source_subfolder, 'extlibs')
        ext_folder = os.path.join(self._source_subfolder, 'ext')
        os.rename(extlibs_folder, ext_folder)
        cmake.configure(build_folder=self._build_subfolder)
        os.rename(ext_folder, extlibs_folder)
        return cmake

    def build(self):
        tools.patch(self._source_subfolder, patch_file="0001-find-libraries.patch")
        if self.settings.compiler == 'Visual Studio':
            with tools.vcvars(self.settings, force=True, filter_known_paths=False):
                cmake = self._configure_cmake()
        else:
            cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern='license.md', dst='licenses', src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
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
                if self.options.window:
                    self.cpp_info.libs.append('opengl32')
                    self.cpp_info.libs.append('gdi32')
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
                self.cpp_info.exelinkflags.append("-ObjC")
                self.cpp_info.sharedlinkflags = self.cpp_info.exelinkflags
