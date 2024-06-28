#!/usr/bin/env python3

'''
IT IS ONLY FIT TO PALLYCON DRM CLI PACKAGER.
IF YOU USE A DIFFERENT PACKAGER, YOU SHOULD NEED TO MODIFY THE CODE.
'''

import glob
import os
import re
import shutil
import sys

VERSION = '1.2'
ENABLE_PRINT_COMPOSING_ITEM = True

class ABComposer():
    def __init__(self):
        self.__compose_dash = False
        self.__compose_hls = False
        self.__compose_cmaf = False
        self.__dash_0_dir = ''
        self.__dash_1_dir = ''
        self.__hls_0_dir = ''
        self.__hls_1_dir = ''
        self.__cmaf_0_dir = ''
        self.__cmaf_1_dir = ''
        self.__root_mpd = []
        self.__dash_files = []
        self.__hls_files = []
        self.__cmaf_files = []
        self.__src0_dir = ''
        self.__src1_dir = ''
        self.__dst_dir = ''
        self.__src0_parent_len = 0
        self.__src1_parent_len = 0
        self.__dst_parent_len = 0
        self.__remove_src = False


    def __check(self, dir_0: str, dir_1: str, dir_dst: str, overwrite: bool) -> bool:
        ## check target directory input by user
        self.__dst_dir = self.__get_full_dir(dir_dst)
        if os.path.exists(self.__dst_dir):
            if not overwrite:
                print(f'target dir, {self.__dst_dir}, is already exist.')
                return False

        ### for print only
        self.__dst_parent_len = self.__dst_dir.rfind(os.path.sep) + 1
        if self.__dst_parent_len <= 0:
            self.__dst_parent_len = 0

        ## check source directory input by user
        self.__src0_dir = self.__get_full_dir(dir_0)
        self.__src1_dir = self.__get_full_dir(dir_1)

        if not os.path.isdir(self.__src0_dir):
            print(f'invalid directory, {self.__src0_dir}')
            return False
        if not os.path.isdir(self.__src1_dir):
            print(f'invalid directory, {self.__src1_dir}')
            return False

        ### for print only
        self.__src0_parent_len = self.__src0_dir.rfind(os.path.sep) + 1
        if self.__src0_parent_len <= 0:
            self.__src0_parent_len = 0
        self.__src1_parent_len = self.__src1_dir.rfind(os.path.sep) + 1
        if self.__src1_parent_len <= 0:
            self.__src1_parent_len = 0

        ## check dash/hls/cmaf manifest existence
        is_valid, self.__compose_dash = self.__check_stream_and_get_root_manifests('dash')
        if not is_valid:
            return False

        is_valid, self.__compose_hls = self.__check_stream_and_get_root_manifests('hls')
        if not is_valid:
            return False

        is_valid, self.__compose_cmaf = self.__check_stream_and_get_root_manifests('cmaf')
        if not is_valid:
            return False

        if not self.__compose_dash and not self.__compose_hls and not self.__compose_cmaf:
            print('no valid dash, hls, nor cmaf.')
            return False

        ## if dash exist, compare 0 and 1 file list.
        if self.__compose_dash:
            self.__dash_files = self.__compare_and_get_filelist(self.__dash_0_dir, self.__dash_1_dir)
            if len(self.__dash_files) < 1:
                print('filelists of dash 0 and 1 are mismatch.')
                return False

        ## if hls exist, compare 0 and 1 file list.
        if self.__compose_hls:
            self.__hls_files = self.__compare_and_get_filelist(self.__hls_0_dir, self.__hls_1_dir)
            if len(self.__hls_files) < 1:
                print('filelists of hls 0 and 1 are mismatch.')
                return False

        ## if cmaf exist, compare 0 and 1 file list.
        if self.__compose_cmaf:
            self.__cmaf_files = self.__compare_and_get_filelist(self.__cmaf_0_dir, self.__cmaf_1_dir)
            if len(self.__cmaf_files) < 1:
                print('filelists of cmaf 0 and 1 are mismatch.')
                return False

        return True


    def __get_full_dir(self, dir_name: str) -> str:
        if dir_name[0] == '~':
            return os.path.expanduser(dir_name)
        else:
            return os.path.abspath(dir_name)


    def __check_stream_and_get_root_manifests(self, stream_type: str) -> 'tuple[bool, bool]':
        stream_root0 = os.path.sep.join([self.__src0_dir, stream_type])
        stream_root1 = os.path.sep.join([self.__src1_dir, stream_type])

        isdir_0 = os.path.isdir(stream_root0)
        isdir_1 = os.path.isdir(stream_root1)

        if not isdir_0 and not isdir_1:
            ## it does not contain 'stream_type' but may contain other stream. so it may not be an error.
            return True, False
        if not isdir_0:
            print(f'{stream_type} 1 exists, but {stream_type} 0 does not.')
            return False, False
        if not isdir_1:
            print(f'{stream_type} 0 exists, but {stream_type} 1 does not.')
            return False, False

        if stream_type == 'dash' or stream_type == 'cmaf':
            mpd_0 = sorted([os.path.basename(x) for x in glob.glob(os.path.sep.join([stream_root0, 'stream*.mpd']))])
            mpd_1 = sorted([os.path.basename(x) for x in glob.glob(os.path.sep.join([stream_root1, 'stream*.mpd']))])

            if len(mpd_0) == 0 and len(mpd_1) == 0:
                print(f'both {stream_type} 0 and 1 do not contain valid mpd.')
                return False, False
            if len(mpd_0) == 0:
                print(f'{stream_type} 0 does not contain valid mpd.')
                return False, False
            if len(mpd_1) == 0:
                print(f'{stream_type} 1 does not contain valid mpd.')
                return False, False
            if mpd_0 != mpd_1:
                print(f'mpd lists in {stream_type} 0 and 1 are mismathced.')
                return False, False

            if stream_type == 'dash':
                self.__dash_0_dir = stream_root0
                self.__dash_1_dir = stream_root1
            else:
                self.__cmaf_0_dir = stream_root0
                self.__cmaf_1_dir = stream_root1
            self.__root_mpd = mpd_0

            return True, True
        elif stream_type == 'hls' or stream_type == 'cmaf':
            m3u8_0 = sorted([os.path.basename(x) for x in glob.glob(os.path.sep.join([stream_root0, 'master*.m3u8']))])
            m3u8_1 = sorted([os.path.basename(x) for x in glob.glob(os.path.sep.join([stream_root1, 'master*.m3u8']))])

            if len(m3u8_0) == 0 and len(m3u8_1) == 0:
                print(f'both {stream_type} 0 and 1 do not contain valid m3u8.')
                return False, False
            if len(m3u8_0) == 0:
                print(f'{stream_type} 0 does not contain valid m3u8.')
                return False, False
            if len(m3u8_1) == 0:
                print(f'{stream_type} 1 does not contain valid m3u8.')
                return False, False
            if m3u8_0 != m3u8_1:
                print(f'm3u8 lists in {stream_type} 0 and 1 are mismathced.')
                return False, False

            self.__hls_0_dir = stream_root0
            self.__hls_1_dir = stream_root1

            return True, True
        else:
            print(f'unsupported stream type, {stream_type}.')
            return False, False


    def __compare_and_get_filelist(self, dir_0: str, dir_1: str) -> list:
        filelist0 = self.__get_filelist(dir_0)
        filelist1 = self.__get_filelist(dir_1)
        if all(x == y for x, y in zip(filelist0, filelist1)):
            return filelist0
        return []


    def __get_filelist(self, dir_src: str) -> list:
        dir_len = len(dir_src)
        filelist = []
        natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\\d+)', s)]
        for (p, _, f) in os.walk(dir_src):
            if len(f) > 0:
                f.sort(key=natsort)
                filelist.append([p[dir_len + 1:], f])
        return filelist


    def __compose_dash_cmaf_unlabeled_a_variant(self) -> None:
        dst_root = ''
        src0_dir = ''
        src1_dir = ''
        src_files = []
        if self.__compose_dash and len(self.__dash_files) > 0:
            dst_root = os.path.sep.join([self.__dst_dir, 'dash'])
            src0_dir = self.__dash_0_dir
            src1_dir = self.__dash_1_dir
            src_files = self.__dash_files

        if self.__compose_cmaf and len(self.__cmaf_files) > 0:
            dst_root = os.path.sep.join([self.__dst_dir, 'cmaf'])
            src0_dir = self.__cmaf_0_dir
            src1_dir = self.__cmaf_1_dir
            src_files = self.__cmaf_files

        if len(dst_root) > 0 and len(src0_dir) > 0 and len(src1_dir) > 0 and len(src_files) > 0:
            os.makedirs(dst_root, exist_ok=True)

            ## rewrite manifest files
            for mpd_file in self.__root_mpd:
                manifest_src = os.path.sep.join([src0_dir, mpd_file])
                manifest_dst = os.path.sep.join([dst_root, mpd_file])
                self.__modify_dash_cmaf_mpd(manifest_src, manifest_dst)
                self.__print_composing_item(manifest_src[self.__src0_parent_len:], manifest_dst[self.__dst_parent_len:], '(modified)')

            ## rename files
            for seg_dir, files in src_files:
                if len(seg_dir) == 0:
                    ## manifest and others
                    for f in files:
                        if f not in self.__root_mpd:
                            ## the manifest has already been rewritten above, so just rename the rest.
                            src = os.path.sep.join([src0_dir, f])
                            dst = os.path.sep.join([dst_root, f])
                            self.__print_composing_item(src[self.__src0_parent_len:], dst[self.__dst_parent_len:])
                            self.__rename_file(src, dst)
                else:
                    os.makedirs(os.path.sep.join([dst_root, seg_dir]), exist_ok=True)

                    ## tracks such as video, audio, and subtitle
                    for f in files:
                        n, e = os.path.splitext(f)
                        if n == 'init':
                            src = os.path.sep.join([src0_dir, seg_dir, f])
                            dst = os.path.sep.join([dst_root, seg_dir, f'_init{e}'])
                            self.__print_composing_item(src[self.__src0_parent_len:], dst[self.__dst_parent_len:])
                            self.__rename_file(src, dst)
                        else:
                            if seg_dir[:5] == 'video':
                                ## rewrite manifests, 'stream.m3u8' and 'iframe.m3u8'
                                if f == 'stream.m3u8' or f == 'iframe.m3u8':
                                    manifest_src = os.path.sep.join([src0_dir, seg_dir, f])
                                    manifest_dst = os.path.sep.join([dst_root, seg_dir, f])
                                    self.__modify_hls_cmaf_m3u8(manifest_src, manifest_dst, True)
                                    self.__print_composing_item(manifest_src[self.__src0_parent_len:], manifest_dst[self.__dst_parent_len:], '(modified)')
                                    continue

                                ## the order of files must be sorted in ascending order.
                                seg_num = int(n[4:])
                                src0 = os.path.sep.join([src0_dir, seg_dir, f])
                                dst0 = os.path.sep.join([dst_root, seg_dir, f'seg_{seg_num - 1}{e}'])
                                src1 = os.path.sep.join([src1_dir, seg_dir, f])
                                dst1 = os.path.sep.join([dst_root, seg_dir, f'b.seg_{seg_num - 1}{e}'])
                                self.__print_composing_item(src0[self.__src0_parent_len:], dst0[self.__dst_parent_len:])
                                self.__print_composing_item(src1[self.__src1_parent_len:], dst1[self.__dst_parent_len:])
                                self.__rename_file(src0, dst0)
                                self.__rename_file(src1, dst1)
                            else:
                                ## rewrite manifest, 'stream.m3u8' and 'subtitle.m3u8'
                                if f == 'stream.m3u8' or f == 'subtitle.m3u8':
                                    manifest_src = os.path.sep.join([src0_dir, seg_dir, f])
                                    manifest_dst = os.path.sep.join([dst_root, seg_dir, f])
                                    self.__modify_hls_cmaf_m3u8(manifest_src, manifest_dst, False)
                                    self.__print_composing_item(manifest_src[self.__src0_parent_len:], manifest_dst[self.__dst_parent_len:], '(modified)')
                                    continue

                                src = os.path.sep.join([src0_dir, seg_dir, f])
                                dst = os.path.sep.join([dst_root, seg_dir, f'{n}_init{e}'])
                                self.__print_composing_item(src[self.__src0_parent_len:], dst[self.__dst_parent_len:])
                                self.__rename_file(src, dst)


    def __compose_hls_unlabeled_a_variant(self) -> None:
        if self.__compose_hls and len(self.__hls_files) > 0:
            dst_root = os.path.sep.join([self.__dst_dir, 'hls'])

            ## rename files
            for seg_dir, files in self.__hls_files:
                if len(seg_dir) == 0:
                    os.makedirs(dst_root, exist_ok=True)

                    ## manifest and others
                    for f in files:
                        src = os.path.sep.join([self.__hls_0_dir, f])
                        dst = os.path.sep.join([dst_root, f])
                        self.__print_composing_item(src[self.__src0_parent_len:], dst[self.__dst_parent_len:])
                        self.__rename_file(src, dst)
                else:
                    os.makedirs(os.path.sep.join([dst_root, seg_dir]), exist_ok=True)

                    ## tracks such as video, audio, and subtitle
                    for f in files:
                        n, e = os.path.splitext(f)
                        if seg_dir[:5] == 'video':
                            if e == '.m3u8':
                                src = os.path.sep.join([self.__hls_0_dir, seg_dir, f])
                                dst = os.path.sep.join([dst_root, seg_dir, f])
                                self.__print_composing_item(src[self.__src0_parent_len:], dst[self.__dst_parent_len:])
                                self.__rename_file(src, dst)
                                continue

                            ## the order of files must be sorted in ascending order.
                            src0 = os.path.sep.join([self.__hls_0_dir, seg_dir, f])
                            dst0 = os.path.sep.join([dst_root, seg_dir, f])
                            src1 = os.path.sep.join([self.__hls_1_dir, seg_dir, f])
                            dst1 = os.path.sep.join([dst_root, seg_dir, f'b.{f}'])
                            self.__print_composing_item(src0[self.__src0_parent_len:], dst0[self.__dst_parent_len:])
                            self.__print_composing_item(src1[self.__src1_parent_len:], dst1[self.__dst_parent_len:])
                            self.__rename_file(src0, dst0)
                            self.__rename_file(src1, dst1)
                        else:
                            ## rewrite manifest, 'stream.m3u8' and 'subtitle.m3u8'
                            if e == '.m3u8':
                                manifest_src = os.path.sep.join([self.__hls_0_dir, seg_dir, f])
                                manifest_dst = os.path.sep.join([dst_root, seg_dir, f])
                                self.__modify_hls_cmaf_m3u8(manifest_src, manifest_dst, False)
                                self.__print_composing_item(manifest_src[self.__src0_parent_len:], manifest_dst[self.__dst_parent_len:], '(modified)')
                                continue

                            if n == 'init':
                                n = ''
                            src = os.path.sep.join([self.__hls_0_dir, seg_dir, f])
                            dst = os.path.sep.join([dst_root, seg_dir, f'{n}_init{e}'])
                            self.__print_composing_item(src[self.__src0_parent_len:], dst[self.__dst_parent_len:])
                            self.__rename_file(src, dst)


    def __modify_dash_cmaf_mpd(self, manifest_src: str, manifest_dst: str) -> None:
        with open(manifest_src, 'rt', encoding='UTF8') as f_in:
            with open(manifest_dst, 'wt', encoding='UTF8') as f_out:
                for line in f_in:
                    if line.find('media="video/') > 0:
                        ## all init files must be 'xxx_init.xxx'
                        line = line.replace('/init.', '/_init.')

                        ## video track must be embedded.
                        ## - It must be '_$Number$' instead of '-$Number$'
                        ## - And it must start from 0
                        line = line.replace('-$Number$.', '_$Number$.').replace('startNumber="1"', 'startNumber="0"')
                    elif line.find('media="audio/') > 0 or line.find('media="subtitle/') > 0:
                        ## all init files must be 'xxx_init.xxx'
                        line = line.replace('/init.', '/_init.')

                        ## the other track may not be embedded.
                        ## to avoid embedding, it applies a little trick of changing all file names as 'init'.
                        line = line.replace('-$Number$.', '-$Number$_init.')

                    f_out.write(line)


    def __modify_hls_cmaf_m3u8(self, manifest_src: str, manifest_dst: str, is_video: bool) -> None:
        init_modified = False
        with open(manifest_src, 'rt', encoding='UTF8') as f_in:
            with open(manifest_dst, 'wt', encoding='UTF8') as f_out:
                for line in f_in:
                    if not init_modified:
                        if line.find('"init.') > 0:
                            ## all init files must be 'xxx_init.xxx'
                            line = line.replace('"init.', '"_init.')
                            init_modified = True

                    if line[:4] == 'seg-':
                        n, _ = os.path.splitext(line)
                        if is_video:
                            ## video track must be embedded.
                            ## - It must be '_$Number$' instead of '-$Number$'
                            ## - And it must start from 0
                            seg_num = int(n[4:])
                            new_seg = f'seg_{seg_num - 1}'
                            line = line.replace(n, new_seg)
                        else:
                            ## the other track may not be embedded.
                            ## to avoid embedding, it applies a little trick of changing all file names as 'init'.
                            line = line.replace(n, f'{n}_init')

                    f_out.write(line)


    def __print_composing_item(self, src: str, dst: str, comment: str='') -> None:
        if ENABLE_PRINT_COMPOSING_ITEM:
            print(' '.join([src, '->', dst, comment]))


    def __rename_file(self, src: str, dst: str) -> None:
        if self.__remove_src:
            os.rename(src, dst)
        else:
            shutil.copy(src, dst)


    def __remove_remaining_dirs(self) -> None:
        if self.__remove_src:
            ## remove remaining files
            shutil.rmtree(self.__src0_dir, ignore_errors=True)
            shutil.rmtree(self.__src1_dir, ignore_errors=True)


    def compose(self, dir_0: str, dir_1: str, dir_dst: str, remove_src: bool, overwrite: bool) -> bool:
        if not self.__check(dir_0, dir_1, dir_dst, overwrite):
            return False

        self.__remove_src = remove_src
        self.__compose_dash_cmaf_unlabeled_a_variant()
        self.__compose_hls_unlabeled_a_variant()
        self.__remove_remaining_dirs()

        return True


def usage():
    print(f'ABComposer v{VERSION}, Copyright 2024 INKA Entworks')
    print(f'  usage: {sys.argv[0]} <stream dir 0> <stream dir 1> <target dir> [--remove_src] [--overwrite]')
    sys.exit(-1)


def main():
    args = sys.argv[1:]

    remove_src = False
    if '--remove_src' in args:
        remove_src = True
        args.remove('--remove_src')

    overwrite = False
    if '--overwrite' in args:
        overwrite = True
        args.remove('--overwrite')

    if len(args) != 3:
        usage()

    composer = ABComposer()
    if not composer.compose(args[0], args[1], args[2], remove_src, overwrite):
        return 1

    return 0


if __name__ == '__main__':
    main()
