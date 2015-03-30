# vim:set ft=python ts=4 sw=4 noet:
APPNAME='nanomsg'

def options(opt):
	opt.load('gnu_dirs')
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
	opt.add_option('--disable-getaddrinfo_a', dest='no_getaddrinfo_a', action='store_false',
		help='Do not use getaddrinfo_a if available [default=use it]')

def configure(conf):
	conf.load('gnu_dirs')
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

	conf.env.build_nanocat     = not conf.options.no_nanocat
	conf.env.nanocat_symlinks  = not conf.options.no_symlinks
	conf.env.build_tcpmuxd     = not conf.options.no_tcpmuxd
	conf.env.use_getaddrinfo_a = not conf.options.no_getaddrinfo_a

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

	conf.check_cc(header_name='time.h', lib='rt', function_name='clock_gettime', uselib_store='RT')
	conf.check_cc(header_name='poll.h', function_name='poll', define_name='NN_HAVE_POLL', mandatory=False)

	if not conf.check_cc(header_name='sys/epoll.h', function_name='epoll_create', define_name='NN_USE_EPOLL', mandatory=False):
		if not conf.check_cc(header_name='sys/types.h sys/event.h sys/time.h', function_name='kqueue', define_name='NN_USE_KQUEUE', mandatory=False):
			conf.define('NN_USE_POLL',1)

	if not conf.check_cc(header_name='sys/types.h ifaddrs.h', function_name='getifaddrs', define_name='NN_USE_IFADDRS', mandatory=False):
		conf.fatal('TODO: check for SIOCGIFADDR or literal ifaddr')

	if conf.check_cc(header_name='sys/socket.h', defines='_GNU_SOURCE', function_name='accept4', define_name='NN_HAVE_ACCEPT4', mandatory=False):
		conf.define('_GNU_SOURCE',1)

	if conf.check_cc(header_name='netdb.h', defines='_GNU_SOURCE', lib='anl', function_name='getaddrinfo_a', define_name='NN_HAVE_GETADDRINFO_A', mandatory=False):
		conf.define('_GNU_SOURCE',1)
	if not conf.env.use_getaddrinfo_a:
		conf.define('NN_DISABLE_GETADDRINFO_A', 1)

	conf.check_cc(header_name='sys/types.h sys/socket.h', function_name='socketpair', define_name='NN_HAVE_SOCKETPAIR', mandatory=False)
	conf.check_cc(header_name='semaphore.h', lib=['rt','pthread'], function_name='sem_wait', define_name='NN_HAVE_SEMAPHORE', mandatory=False)

	conf.check_cc(msg='Checking for gcc atomic builtins', fragment='''
		#include <stdint.h>
		int main()
		{
			volatile uint32_t n = 0;
			__sync_fetch_and_add (&n, 1);
			__sync_fetch_and_sub (&n, 1);
			return 0;
		}''', define_name='NN_HAVE_GCC_ATOMIC_BUILTINS', mandatory=False)

	conf.check_cc(msg='Checking for atomic solaris', fragment='''
		#include <atomic.h>
		int main()
		{
			uint32_t value;
			atomic_cas_32 (&value, 0, 0);
			return 0;
		}''', define_name='NN_HAVE_ATOMIC_SOLARIS', mandatory=False)

	conf.check_cc(msg='Checking for msghdr.msg_control', fragment='''
		#include <sys/socket.h>
		int main()
		{
			struct msghdr hdr;
			hdr.msg_control = 0;
			return 0;
		}''', define_name='NN_HAVE_MSG_CONTROL', mandatory=False)

	if conf.is_defined('NN_HAVE_EVENTFD'):
		conf.define('NN_USE_EVENTFD', 1)
	elif conf.is_defined('NN_HAVE_PIPE'):
		conf.define('NN_USE_PIPE', 1)
	elif conf.is_defined('NN_HAVE_SOCKETPAIR'):
		conf.define('NN_USE_SOCKETPAIR', 1)

def build(bld):

	nanomsg_core    = [ ('src/core/%s.c'%f) for f in 'ep epbase global pipe poll sock sockbase symbol'.split() ]
	nanomsg_devices = [ ('src/devices/%s.c'%f) for f in 'device tcpmuxd'.split() ]
	nanomsg_aio     = [ ('src/aio/%s.c'%f) for f in 'ctx fsm poller pool timer timerset usock worker'.split() ]
	nanomsg_utils   = [ ('src/utils/%s.c'%f) for f in '''
		alloc atomic chunk chunkref clock closefd
		efd err glock hash list msg mutex queue
		random sem sleep stopwatch thread wire'''.split() ]

	protocols_utils    = [ ('src/protocols/utils/%s.c'%f) for f in 'dist excl fq lb priolist'.split() ]
	protocols_bus      = [ ('src/protocols/bus/%s.c'%f) for f in 'bus xbus'.split() ]
	protocols_pipeline = [ ('src/protocols/pipeline/%s.c'%f) for f in 'push pull xpull xpush'.split() ]
	protocols_pair     = [ ('src/protocols/pair/%s.c'%f) for f in 'pair xpair'.split() ]
	protocols_pubsub   = [ ('src/protocols/pubsub/%s.c'%f) for f in 'pub sub trie xpub xsub'.split() ]
	protocols_reqrep   = [ ('src/protocols/reqrep/%s.c'%f) for f in 'req rep task xrep xreq'.split() ]
	protocols_survey   = [ ('src/protocols/survey/%s.c'%f) for f in 'respondent surveyor xrespondent xsurveyor'.split() ]

	nanomsg_protocols = protocols_utils + protocols_bus + protocols_pipeline + protocols_pair + protocols_pubsub + protocols_reqrep + protocols_survey

	transports_utils  = [ ('src/transports/utils/%s.c'%f) for f in 'backoff dns iface literal port streamhdr base64'.split() ]
	transports_inproc = [ ('src/transports/inproc/%s.c'%f) for f in 'binproc cinproc inproc ins msgqueue sinproc'.split() ]
	transports_ipc    = [ ('src/transports/ipc/%s.c'%f) for f in 'aipc bipc cipc ipc sipc'.split() ]
	transports_tcp    = [ ('src/transports/tcp/%s.c'%f) for f in 'atcp btcp ctcp stcp tcp'.split() ]
	transports_ws     = [ ('src/transports/ws/%s.c'%f) for f in 'aws bws cws sws ws ws_handshake sha1'.split() ]
	transports_tcpmux = [ ('src/transports/tcpmux/%s.c'%f) for f in 'atcpmux btcpmux ctcpmux stcpmux tcpmux'.split() ]

	nanomsg_transports = transports_utils + transports_inproc + transports_ipc + transports_tcp + transports_ws + transports_tcpmux

	bld.shlib(
			target = 'nanomsg',
			source = nanomsg_core + nanomsg_aio + nanomsg_utils + nanomsg_protocols + nanomsg_transports +nanomsg_devices,
			defines = 'NN_EXPORTS',
			vnum = bld.env.nn_abi_version,
			use = 'PTHREAD RT GETADDRINFO_A'
			)

	#linkflags = '-Wl,-no-undefined -Wl,-version-info=%s' % bld.env.nn_libtool_version,

	if bld.env.build_nanocat:
		bld.program(
				target = 'nanocat',
				source = 'tools/nanocat.c tools/options.c',
				use = 'nanomsg'
				)

	if bld.env.build_tcpmuxd:
		bld.program(
				target = 'tcpmuxd',
				source = 'tools/tcpmuxd.c',
				use = 'nanomsg'
				)

	all_perfs = '''
		perf/inproc_lat
		perf/inproc_thr
		perf/local_lat
		perf/remote_lat
		perf/local_thr
		perf/remote_thr
		'''.split()

	for t in all_perfs:
		bld.program(
				target = t,
				source = t+'.c',
				use = 'nanomsg',
				install_path = None
				)

	all_tests = '''
		tests/inproc
		tests/inproc_shutdown
		tests/ipc
		tests/ipc_shutdown
		tests/ipc_stress
		tests/tcp
		tests/tcp_shutdown
		tests/ws
		tests/tcpmux
		tests/pair
		tests/pubsub
		tests/reqrep
		tests/pipeline
		tests/survey
		tests/bus
		tests/block
		tests/term
		tests/timeo
		tests/iovec
		tests/msg
		tests/prio
		tests/poll
		tests/device
		tests/emfile
		tests/domain
		tests/trie
		tests/list
		tests/hash
		tests/symbol
		tests/separation
		tests/zerocopy
		tests/shutdown
		tests/cmsg'''.split()

	for t in all_tests:
		bld.program(
				target = t,
				source = t+'.c',
				use = 'nanomsg',
				install_path = None
				)

	if bld.env.build_doc:
		bld.recurse('doc')
