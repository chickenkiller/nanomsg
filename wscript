# vim:set ft=python ts=4 sw=4 noet:
APPNAME='nanomsg'

def options(opt):
	opt.load('compiler_c')	
	opt.add_option('--debug', dest='debug', action='store_true',
		help='Enable debugging information [default=no]')
	opt.add_option('--enable-doc', dest='doc', action='store_true',
		help='Build documentation [default=no]')
	opt.add_option('--disable-nanocat', dest='no_nanocat', action='store_false',
		help='Do not build nanocat executable [default=build it]')
	opt.add_option('--disable-symlinks', dest='no_symlinks', action='store_false',
		help='Do not make nn_xxx symlinks for nanocat [default=make them]')
	opt.add_option('--disable-tcpmuxd', dest='no_tcpmuxd', action='store_false',
		help='Do not build tcpmuxd executable [default=build it]')

def configure(conf):
	conf.load('compiler_c')
	conf.env.nn_abi_version = conf.cmd_and_log('./abi_version.sh')
	conf.env.nn_package_version = conf.cmd_and_log('./package_version.sh')
	conf.env.nn_libtool_version = conf.cmd_and_log(['./abi_version.sh','-libtool'])
	conf.msg('nanomsg package version', conf.env.nn_package_version)
	conf.msg('nanomsg ABI version', conf.env.nn_abi_version)

	if conf.env.CC_NAME == 'gcc':
		conf.define('NN_HAVE_GCC',1)
	elif conf.env.CC_NAME == 'icc':
		conf.define('NN_HAVE_ICC',1)
	elif conf.env.CC_NAME == 'sun':
		conf.define('NN_HAVE_SUN_STUDIO',1)
	elif conf.env.CC_NAME == 'clang':
		conf.define('NN_HAVE_CLANG',1)

	if conf.options.debug:
		if conf.env.CC_NAME == 'sun':
			conf.env.append_unique('CFLAGS','-g0')
		else:
			conf.env.append_unique('CFLAGS',['-g','-O0'])
		conf.define('NN_DEBUG',1)

	conf.env.build_doc = False
	if conf.options.doc:
		if conf.find_program('asciidoc', mandatory=False) and conf.find_program('xmlto', mandatory=False):
			conf.env.build_doc = True

	conf.env.build_nanocat    = not conf.options.no_nanocat
	conf.env.nanocat_symlinks = not conf.options.no_symlinks
	conf.env.build_tcpmuxd    = not conf.options.no_tcpmuxd

	if conf.env.DEST_OS == 'linux':
		conf.define('NN_HAVE_LINUX',1)
	if conf.env.DEST_OS == 'win32':
		conf.define('NN_HAVE_WINDOWS',1)
		conf.define('NN_HAVE_MINGW',1)
		conf.define('_WIN32_WINNT',0x0600)
		conf.env.append_unique('LIBS',['ws2_32','Mswsock'])
	if conf.env.DEST_OS == 'darwin':
		conf.define('NN_HAVE_OSX',1)
	if conf.env.DEST_OS == 'freebsd':
		conf.define('NN_HAVE_FREEBSD',1)
	if conf.env.DEST_OS == 'netbsd':
		conf.define('NN_HAVE_NETBSD',1)
	if conf.env.DEST_OS == 'openbsd':
		conf.define('NN_HAVE_OPENBSD',1)
	if conf.env.DEST_OS == 'hpux':
		conf.define('NN_HAVE_HPUX',1)
	if conf.env.DEST_OS == 'sunos':
		conf.define('NN_HAVE_SOLARIS',1)
		conf.check_cc(lib='socket',header_name='sys/types.h sys/socket.h',function_name='socket')
		conf.check_cc(lib='nsl',header_name='netdb.h',function_name='gethostbyname')
	if conf.env.DEST_OS == 'qnx':
		conf.define('NN_HAVE_QNX',1)
		conf.check_cc(lib='socket',header_name='sys/types.h sys/socket.h',function_name='socket')

	conf.parse_flags('-pthread', 'PTHREAD')

	for h in '''netinet/in.h netdb.h arpa/inet.h unistd.h
				sys/socket.h sys/ioctl.h'''.split():
		conf.check_cc(header_name=h)
	conf.check_cc(header_name='stdint.h', define_name='NN_HAVE_STDINT', mandatory=False)
	conf.check_cc(header_name='sys/eventfd.h', function_name='eventfd', define_name='NN_HAVE_EVENTFD', mandatory=False)
	conf.check_cc(header_name='unistd.h', function_name='pipe', define_name='NN_HAVE_PIPE', mandatory=False)
	if conf.check_cc(header_name='unistd.h', function_name='pipe2', defines='_GNU_SOURCE', define_name='NN_HAVE_PIPE2', mandatory=False):
		conf.define('_GNU_SOURCE',1)
	conf.check_cc(header_name='sys/time.h', function_name='gethrtime', define_name='NN_HAVE_GETHRTIME', mandatory=False)
	conf.check_cc(msg='Checking for CLOCK_MONOTONIC', fragment='''
			#include <time.h>
			int main() {
			struct timespec ts;
			clock_gettime(CLOCK_MONOTONIC, &ts);
			return 0;
			}''', define_name='NN_HAVE_CLOCK_MONOTONIC', mandatory=False)

	conf.check_cc(header_name='time.h', lib='rt', function_name='clock_gettime')
	conf.check_cc(header_name='poll.h', function_name='poll', define_name='NN_HAVE_POLL', mandatory=False)
	if not conf.check_cc(header_name='sys/epoll.h', function_name='epoll_create', define_name='NN_USE_EPOLL', mandatory=False):
		if not conf.check_cc(header_name='sys/types.h sys/event.h sys/time.h', function_name='kqueue', define_name='NN_USE_KQUEUE', mandatory=False):
			conf.define('NN_USE_POLL',1)	
	if not conf.check_cc(header_name='sys/types.h ifaddrs.h', function_name='getifaddrs', define_name='NN_USE_IFADDRS', mandatory=False):
		conf.fatal('TODO: check for SIOCGIFADDR or literal ifaddr')
	if conf.check_cc(header_name='sys/socket.h', defines='_GNU_SOURCE', function_name='accept4', define_name='NN_HAVE_ACCEPT4', mandatory=False):
		conf.define('_GNU_SOURCE',1)

def build(bld):
	pass

