#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools, RunEnvironment
import os


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake", "cmake_find_package", "cmake_find_package_multi", "xcode"

    def build(self):
        for generator in ["cmake", "cmake_targets", "cmake_find_package", "cmake_find_package_multi"]:
            self.output.info("test generator %s" % generator)
            cmake = CMake(self)
            cmake.definitions['CONAN_CMAKE_GENERATOR'] = generator
            cmake.definitions['WITH_WINDOW'] = self.options['sfml'].window
            cmake.definitions['WITH_GRAPHICS'] = self.options['sfml'].graphics
            cmake.definitions['WITH_AUDIO'] = self.options['sfml'].audio
            cmake.definitions['WITH_NETWORK'] = self.options['sfml'].network
            cmake.configure(build_folder=generator)
            cmake.build()
        if tools.is_apple_os(self.settings.os):
            xcodeproj = os.path.join(self.source_folder, "conan-sfml-test", "conan-sfml-test.xcodeproj")
            xcconfig = os.path.join(self.build_folder, "conanbuildinfo.xcconfig")
            self.run('xcodebuild -configuration conanbuildinfo -xcconfig "%s" -project "%s"' % (xcconfig, xcodeproj))

    def test(self):
        for generator in ["cmake", "cmake_targets", "cmake_find_package", "cmake_find_package_multi"]:
            bin_path = os.path.join(generator, "bin", "test_package")
            self.run(bin_path, run_environment=True)
