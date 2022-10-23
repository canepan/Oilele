try:
    from configargparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
except ModuleNotFoundError:
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import sys

from . import logging_utils


class LoggingArgumentParser(ArgumentParser):
    def __init__(self, *args, app_name: str = None, **kwargs):
        super(LoggingArgumentParser, self).__init__(*args, **kwargs)
        try:
            self.add_argument('--config', '-c', is_config_file=True, help='{} config file'.format(app_name))
        except TypeError:
            pass
        g = self.add_mutually_exclusive_group()
        g.add_argument('-q', '--quiet', action='store_true')
        g.add_argument('-v', '--verbose', action='store_true')
        if app_name is not None:
            self.app_name = app_name
        else:
            fr = next(sys._current_frames().values().__iter__()).f_back
            self.app_name = fr.f_globals['__name__'] if fr else None

    def parse_args(self, *args, **kwargs):
        cfg = super(LoggingArgumentParser, self).parse_args(*args, **kwargs)
        log_file = f'{self.app_name}.log' if self.app_name else None
        cfg.log = logging_utils.get_logger(self.app_name, verbose=cfg.verbose, quiet=cfg.quiet, with_file=log_file)
        return cfg


def arg_parser(description: str) -> ArgumentParser:
    parser = ArgumentParser(description=description, formatter_class=ArgumentDefaultsHelpFormatter)
    return parser


def with_quiet_verbose(
    app_name: str, parser: ArgumentParser = None, argv: list = None, logfile: str = None
) -> Namespace:
    """
    Optionally create a parser, add --quiet/--verbose and return parsed args with `.log`
    """
    if not parser:
        parser = arg_parser(description='{} arguments'.format(app_name))
    parser.add_argument('--config', '-c', is_config_file=True, help='{} config file'.format(app_name))
    g = parser.add_mutually_exclusive_group()
    g.add_argument('-q', '--quiet', action='store_true')
    g.add_argument('-v', '--verbose', action='store_true')
    if argv is None:
        argv = sys.argv[1:]
    cfg = parser.parse_args(argv)
    if logfile:
        logfile = logfile.format(**cfg.__dict__)
    cfg.log = logging_utils.get_logger(app_name, verbose=cfg.verbose, quiet=cfg.quiet, with_file=logfile)
    return cfg
