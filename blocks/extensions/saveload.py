"""Extensions for saving and loading the state of a training process."""
import dill
import logging
import traceback

from blocks.extensions import SimpleExtension, TrainingExtension
from blocks.serialization import MainLoopStateManager

logger = logging.getLogger(__name__)

LOADED_FROM = "loaded_from"
SAVING_DONE_TO = "saving_done_to"


class SerializeMainLoop(SimpleExtension):
    """Saves a pickled version of the main loop to the disk.

    The pickled main loop can be later reloaded and training can be
    resumed.

    Parameters
    ----------
    path : str
        The destination path for pickling.

    Notes
    -----
    Instead of the standard pickling library, the dill package is used.

    Using pickling for saving the whole main loop object comes with
    certain limitations:

    * Theano computation graphs build in the GPU-mode
      (`theano.config.device == "gpu"`) can not be used in the usual mode
      (and vice-versa). Therefore using this extension binds you to using
      only one kind of device.


    """
    def __init__(self, path, **kwargs):
        kwargs.setdefault("after_training", True)
        super(SerializeMainLoop, self).__init__(**kwargs)
        self.path = path

    def do(self, callback_name, *args):
        """Pickle the main loop object to the disk."""
        try:
            self.main_loop.log.current_row[SAVING_DONE_TO] = self.path
            with open(self.path, "wb") as destination:
                dill.dump(self.main_loop, destination,
                          fmode=dill.CONTENTS_FMODE)
        except:
            self.main_loop.log.current_row[SAVING_DONE_TO] = None


class LoadTrainingState(TrainingExtension):
    def __init__(self, state_path):
        self.manager = MainLoopStateManager(state_path)

    def before_training(self):
        logger.info("Loading the state from {} into the main loop"
                    .format(self.manager.folder))
        try:
            self.manager.load_to(self.main_loop)
            self.main_loop.log.current_row[LOADED_FROM] = self.manager.folder
        except:
            logger.error("Failed to load the state:\n{}"
                         .format(traceback.format_exc()))


class SaveTrainingState(SimpleExtension):
    def __init__(self, state_path, **kwargs):
        kwargs.setdefault("after_training", True)
        super(SaveTrainingState, self).__init__(**kwargs)
        self.manager = MainLoopStateManager(state_path)

    def do(self, callback_name, **kwargs):
        try:
            self.main_loop.log.current_row[SAVING_DONE_TO] = (
                self.manager.folder)
            self.manager.save(self.main_loop)
        except:
            self.main_loop.log.current_row[SAVING_DONE_TO] = None
