import inject
import os.path
import logging
from freyja.config import Config
from freyja.graph import Singleton
from hephaestus.steps import (
    FindOrCopyApp,
    FindOrCopyFilesByName,
    SBApi,
    FindOrCreateProject,
)


class Context(metaclass=Singleton):
    """Singleton class to store global variables for automation,
    such as execution project, apps, and reference files.
    
    WARNING: Use context carefully in multi-threaded environments.
    It should be initialized once at the beginning of the automation
    and then all access to it must be read-only. Otherwise
    race conditions can cause problems that are very
    difficult to debug."""

    def __init__(self):
        self.config = inject.instance(Config)
        self.project = None
        self.apps = {}
        self.refs = {}

    def initialize(self, project_name):
        "Initializes context. Read-only after this point." ""

        self.project = FindOrCreateProject(
            billing_group_name=self.get_first_billing_group(), name=project_name
        ).project

        self.stage_apps()
        self.stage_reference_files()

    def get_first_billing_group(self):
        "Finds and returns first billing group, if any."

        for bg in SBApi().billing_groups.query().all():
            logging.info(f"Using billing group '{bg.name}'")
            return bg.name

    def stage_apps(self):
        "Copy and cache all apps defined in config file"

        for app_name, app_id in self.config.apps.data.items():
            self.apps[app_name] = FindOrCopyApp(
                name_=f"FindOrCopyApp-{app_name}",
                app_id=app_id,
                to_project=self.project,
            ).app

    def stage_reference_files(self):
        "Copy and cache all reference files defined in config file"

        for ref_name, file_path in self.config.reference_files.data.items():
            self.refs[ref_name] = self.stage_reference_file(ref_name, file_path)

    def stage_reference_file(self, ref_name, file_path):
        """Split file path into project id and filename and copy file to
        execution project. Folder support not yet implemented."""

        ref_project_id, file_name = os.path.split(file_path)
        ref_project = SBApi().projects.get(id=ref_project_id)

        return FindOrCopyFilesByName(
            name_=f"CopyRef-{ref_name}",
            names=[file_name],
            from_project=ref_project,
            to_project=self.project,
        ).copied_files[0]
