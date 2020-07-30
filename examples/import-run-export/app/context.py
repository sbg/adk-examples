import inject
import os.path
from freyja.config import Config
from freyja.graph import Singleton
from hephaestus.steps import (
    FindOrCopyApp,
    FindOrCopyFilesByName,
    SBApi,
    FindOrCreateProject,
)


class Context(metaclass=Singleton):
    """Singleton class that holds data that is accessed 
    frequently throughout the automation, such as execution project, 
    CWL apps, and reference files.
    
    WARNING: Use contexts carefully in multi-threaded environments.
    It should be initialized once at the beginning of execution
    and then all access to it must be read-only. Otherwise
    race conditions can cause nasty problems that are 
    difficult to debug."""

    def __init__(self):
        self.config = inject.instance(Config)
        self.project = None
        self.apps = {}
        self.refs = {}

    def initialize(self, project_name):
        self.project = FindOrCreateProject(
            billing_group_name=self.get_first_billing_group(), name=project_name
        ).project

        self.stage_apps()
        self.stage_references()

        return self

    def get_first_billing_group(self):
        for bg in SBApi().billing_groups.query().all():
            return bg.name

    def stage_apps(self):
        for app_name, app_id in self.config.apps.data.items():
            self.apps[app_name] = FindOrCopyApp(
                f"FindOrCopyApp-{app_name}", app_id=app_id, to_project=self.project
            ).app

    def stage_references(self):
        for ref_name, file_path in self.config.reference_files.data.items():
            self.refs[ref_name] = self.stage_reference_file(ref_name, file_path)

    def stage_reference_file(self, ref_name, file_path):
        ref_project_id, file_name = os.path.split(file_path)
        ref_project = SBApi().projects.get(id=ref_project_id)

        return FindOrCopyFilesByName(
            f"CopyRef-{ref_name}",
            names=[file_name],
            from_project=ref_project,
            to_project=self.project,
        ).copied_files[0]
