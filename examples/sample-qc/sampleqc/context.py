import inject
import os.path
import logging
from freyja.config import Config
from freyja.graph import Singleton
from hephaestus import SBApi
from hephaestus.steps import (
    FindOrCopyApp,
    FindOrCopyFilesByName,
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
        """Copy and cache all reference files defined in config file.
        Group by source location and copy in bulk to increase efficiency."""
        
        ref_files = self.config.reference_files.data
        
        f2ref, sources = {}, {}
        for ref_name, file_path in ref_files.items():
            
            project = "/".join(file_path.split("/")[0:2])
            path = "/".join(file_path.split("/")[2:-1])
            name = file_path.split("/")[-1]
            
            f2ref[name] = ref_name
            key = project + "|" + path
            src = {"ref_name": ref_name, "filename": name}
            
            if key in sources:
                sources[key].append(src)
            else:
                sources[key] = [src]
                
        for loc, items in sources.items():
            project, path = loc.split("|")
            
            copied_files = FindOrCopyFilesByName(
                name_=f"CopyFiles-" + loc,
                names=[i["filename"] for i in items],
                from_project=SBApi().projects.get(id=project),
                from_path=path if path else None,
                to_project=self.project,
                to_path="reference_files"
            ).copied_files
            
            for ref_name, file in zip([i["ref_name"] for i in items], copied_files):
                logging.info("Reference staged: %s -> %s" \
                             % (f2ref[file.name], file.name))
                self.refs[f2ref[file.name]] = file
