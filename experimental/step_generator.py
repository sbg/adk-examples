# DISCLAIMER: This code is experimental and currently not officially supported by SB.
# It takes a CWL app as input and creates automation step class as output, eliminating
# the need for manual app wrapper step.
#
# Usage example:
#
# FastQC = generate_cwl_step(
#     app="admin/sbg-public-data/fastqc-0-11-4",
#     project=my_execution_project
# )
# fastqc = FastQC(fastq_file=fastq_file)

import datetime
from hephaestus.steps import FindOrCreateAndRunTask, FindOrCopyApp, FindOrCopyFiles
from freyja import Step, Input, Output, Optional
from hephaestus.sb_api import SBApi
from hephaestus.enums import StepOptions
from experimental.enums import CWLTypes, CWLDraft2Types
import sevenbridges as sb
import logging

logger = logging.getLogger(__name__)


def get_type(outp_id, app_raw):
    workflow = "Workflow"
    if app_raw["cwlVersion"] == "sbg:draft-2":
        source = "source"
        source_split = "."
        array_type = CWLDraft2Types.Array[0]
        prefix = "#"

        def return_expr(out_type):
            return [t for t in out_type if t != "null"][0]

    elif app_raw["cwlVersion"] == "v1.0":
        source = "outputSource"
        source_split = "/"
        array_type = CWLTypes.Array[0]
        prefix = ""

        def return_expr(out_type):
            return out_type

    else:
        logger.error("CWL version not recognised")
        raise Exception("CWL version not recognised")

    if app_raw["class"] == workflow:
        steps_dict = {}
        for step in app_raw["steps"]:
            steps_dict[step["id"]] = step
        for outp in app_raw["outputs"]:
            if outp["id"] == outp_id:
                source = outp[source][0]
                source_tool_id = source.split(source_split)[0]
                source_tool = steps_dict[source_tool_id]
                if "scatter" in source_tool:
                    return array_type
                source_output = source.split(source_split)[1]
                if source_tool["run"]["class"] == workflow:
                    return get_type(prefix + source_output, source_tool["run"])
                else:
                    for output in source_tool["run"]["outputs"]:
                        if output["id"] == prefix + source_output:
                            return return_expr(output["type"])
    else:
        output = None
        for outp in app_raw["outputs"]:
            if outp["id"] == outp_id:
                output = outp
                break
        return return_expr(output["type"])


def get_suggested_values(app):
    """
    Returns a dictionary with suggested values of an app
    :param app: sbg api application object
    :return: dictionary with key value pairs
    """
    input_dict = {}
    sug_value_key = "sbg:suggestedValue"
    for app_input in app.raw["inputs"]:
        if sug_value_key in app_input:
            if app.raw["cwlVersion"] == "v1.0":
                id = app_input["id"]
            elif app.raw["cwlVersion"] == "sbg:draft-2":
                id = app_input["id"][1:]
            else:
                raise Exception("CWL version not recognized")

            value = app_input[sug_value_key]
            if isinstance(value, list):
                value_list = []
                for e in value:
                    if isinstance(e, dict):
                        if "class" in e:
                            if e["class"] == "File":
                                value_list.append((e["path"], e["name"]))
                value = [sb.File(id=f[0], name=f[1]) for f in value_list]
            elif isinstance(value, dict):
                if "class" in value:
                    if value["class"] == "File":
                        value = sb.File(id=value["path"], name=value["name"])

            input_dict[id] = value

    return input_dict


def dict_to_list(in_dict):
    """
    Turns dictionary to a list
    :param in_dict: input dictionary
    :return: list
    """
    output_list = []
    if isinstance(in_dict, dict):
        for key in in_dict:
            if isinstance(in_dict[key], dict) or isinstance(in_dict[key], list):
                output_list.extend(dict_to_list(in_dict[key]))
            else:
                output_list.append(in_dict[key])
    elif isinstance(in_dict, list):
        for elem in in_dict:
            if isinstance(elem, dict) or isinstance(elem, list):
                output_list.extend(dict_to_list(elem))
            else:
                output_list.append(elem)

    return output_list


def remap_to_dict(in_list, orig_dict):
    """
    Remaps a list to dictionary
    :param in_list: input list
    :param orig_dict: original dictionary for reference
    :return: new dictionary
    """
    if isinstance(orig_dict, dict):
        new_dict = {}
        for key in orig_dict:
            if isinstance(orig_dict[key], dict) or isinstance(orig_dict[key], list):
                new_dict[key] = remap_to_dict(in_list, orig_dict[key])
            else:
                if orig_dict[key] in in_list:
                    new_dict[key] = in_list[in_list.index(orig_dict[key])]
                else:
                    raise Exception("Element not found in list")
    elif isinstance(orig_dict, list):
        new_dict = []
        for elem in orig_dict:
            if isinstance(elem, dict) or isinstance(elem, list):
                new_dict.append(remap_to_dict(in_list, elem))
            else:
                if elem in in_list:
                    new_dict.append(in_list[in_list.index(elem)])
                else:
                    raise Exception("Element not found in list")
    else:
        raise Exception("Input dict faulty")
    return new_dict


def run_task(self):
    """
    Default execute function for the autogenerated freyja Step
    :param self:
    """

    input_dict = {}

    for inp in self.app_.raw["inputs"]:
        if self.app_.raw["cwlVersion"] == "v1.0":
            inp_id = inp["id"]
        elif self.app_.raw["cwlVersion"] == "sbg:draft-2":
            inp_id = inp["id"][1:]
        else:
            raise Exception("CWL version not recognized")
        if not isinstance(getattr(self, inp_id), type(None)):
            input_dict[inp_id] = getattr(self, inp_id)

    refresh = StepOptions.TASK_REFRESH_PERIOD
    # disable_batch fixed to True for automation purposes
    task = FindOrCreateAndRunTask(
        f"FindOrCreateAndRunTask {self.name_}",
        new_name=self.name_ + " at: " + str(datetime.datetime.now()),
        inputs=input_dict,
        app=self.app_,
        in_project=self.project_,
        task_status_refresh_period=refresh,
        disable_batch=True,
    ).finished_task

    out = task.outputs
    out_list = dict_to_list(out)
    # Clearing empty outputs for bulk get
    out_list = [e for e in out_list if e is not None]
    out_files_list = [f for f in out_list if isinstance(f, sb.File)]
    out_other_list = [f for f in out_list if not isinstance(f, sb.File)]
    del out_list
    loaded_out_list = []

    for i in range(0, len(out_files_list), 100):
        legal_bulk = out_files_list[i : i + 100]
        loaded_out_list.extend(SBApi().files.bulk_get(legal_bulk))

    errors = [b.error.message for b in loaded_out_list if b.error]
    if errors:
        raise Exception("There were errors with bulk get: {}".format("; ".join(errors)))
    loaded_out_list = [f.resource for f in loaded_out_list]
    loaded_out_list.extend(out_other_list)
    # Adding a "None" element for remapping empty outputs
    loaded_out_list.append(None)

    out = remap_to_dict(loaded_out_list, out)

    for outp in self.app_.raw["outputs"]:
        if self.app_.raw["cwlVersion"] == "v1.0":
            outp_id = outp["id"]
        elif self.app_.raw["cwlVersion"] == "sbg:draft-2":
            outp_id = outp["id"][1:]
        else:
            raise Exception("CWL version not recognized")
        if out[outp_id]:
            setattr(self, outp_id, out[outp_id])
        else:
            setattr(self, outp_id, None)


def generate_cwl_step(
    app, project, execute_method=run_task, import_suggested_files=True
):
    """
    Generates a Step object with Input and Output ports named the same
    as the given CWL app
    :param app: App to wrap
    :param project: Project where the app resides
    :param execute_method: Execute method to be used in this step.
    :param import_suggested_files: Import suggested files in the project
    :return: Freyja Step
    """
    input_dict = {}
    outp_dict = {}

    if isinstance(app, sb.App):
        pass
    elif isinstance(app, str):
        app = FindOrCopyApp(app_id=app, to_project=project, name_=f"Copy {app}").app

    suggested_values = get_suggested_values(app)

    for key in suggested_values:
        if isinstance(suggested_values[key], list):
            if isinstance(suggested_values[key][0], sb.File):
                if import_suggested_files:
                    suggested_values[key] = FindOrCopyFiles(
                        "Copying suggested file {} for {}".format(key, app.id),
                        files=suggested_values[key],
                        to_project=project,
                    ).copied_files
                else:
                    suggested_values[key] = None
        elif isinstance(suggested_values[key], sb.File):
            if import_suggested_files:
                suggested_values[key] = FindOrCopyFiles(
                    "Copying suggested file {} for {}".format(key, app.id),
                    files=[suggested_values[key]],
                    to_project=project,
                ).copied_files[0]
            else:
                suggested_values[key] = None
    cwl_version = app.raw["cwlVersion"]
    if cwl_version == "v1.0":
        for inp in app.raw["inputs"]:
            inp_id = inp["id"]
            inp_type = inp["type"]
            value = None
            if inp_id in suggested_values:
                value = suggested_values[inp_id]
            if isinstance(inp_type, str) or isinstance(inp_type, dict):
                if inp_type in CWLTypes.File:
                    input_dict[inp_id] = Input(Optional[sb.File], default=value)
                elif inp_type in CWLTypes.Array:
                    input_dict[inp_id] = Input(Optional[list], default=value)
                elif inp_type in CWLTypes.String:
                    input_dict[inp_id] = Input(Optional[str], default=value)
                elif inp_type in CWLTypes.Int:
                    input_dict[inp_id] = Input(Optional[int], default=value)
                elif inp_type in CWLTypes.Bool:
                    input_dict[inp_id] = Input(Optional[bool], default=value)
                elif inp_type in CWLTypes.Float:
                    input_dict[inp_id] = Input(Optional[float], default=value)
            elif isinstance(inp_type, list):
                if inp_type[1] in CWLTypes.Array:
                    input_dict[inp_id] = Input(Optional[list], default=value)
                elif inp_type[1]["type"] == "enum":
                    input_dict[inp_id] = Input(Optional[str], default=value)

            else:
                if inp["type"][1]["type"] == "enum":
                    input_dict[inp_id] = Input(Optional[str], default=value)

        for outp in app.raw["outputs"]:
            outp_id = outp["id"]
            outp_type = get_type(outp_id, app.raw)
            if outp_type in CWLTypes.File:
                outp_dict[outp_id] = Output(Optional[sb.File])
            elif outp_type in CWLTypes.Array:
                outp_dict[outp_id] = Output(Optional[list])
            elif outp_type in CWLTypes.String:
                outp_dict[outp_id] = Output(Optional[str])
            elif outp_type in CWLTypes.Int:
                outp_dict[outp_id] = Output(Optional[int])
            elif outp_type in CWLTypes.Bool:
                outp_dict[outp_id] = Output(Optional[bool])
            elif outp_type in CWLTypes.Float:
                outp_dict[outp_id] = Output(Optional[float])

    elif cwl_version == "sbg:draft-2":
        for inp in app.raw["inputs"]:
            inp_id = inp["id"][1:]
            inp_type = [t for t in inp["type"] if t != "null"][0]
            value = None
            if inp_id in suggested_values:
                value = suggested_values[inp_id]
            if inp_type in CWLDraft2Types.File:
                input_dict[inp_id] = Input(Optional[sb.File], default=value)
            elif inp_type in CWLDraft2Types.Array:
                input_dict[inp_id] = Input(Optional[list], default=value)
            elif inp_type in CWLDraft2Types.String:
                input_dict[inp_id] = Input(Optional[str], default=value)
            elif inp_type in CWLDraft2Types.Int:
                input_dict[inp_id] = Input(Optional[int], default=value)
            elif inp_type in CWLDraft2Types.Bool:
                input_dict[inp_id] = Input(Optional[bool], default=value)
            elif inp_type in CWLDraft2Types.Float:
                input_dict[inp_id] = Input(Optional[float], default=value)
            elif "type" in inp_type:
                if inp_type["type"] == "enum":
                    input_dict[inp_id] = Input(Optional[str], default=value)
                elif inp_type["type"] == "array":
                    input_dict[inp_id] = Input(Optional[list], default=value)
                elif inp_type["type"] == "record":
                    input_dict[inp_id] = Input(Optional[dict], default=value)

        for outp in app.raw["outputs"]:
            outp_id = outp["id"][1:]
            outp_type = get_type(outp["id"], app.raw)
            if outp_type in CWLDraft2Types.File:
                outp_dict[outp_id] = Output(Optional[sb.File])
            elif outp_type in CWLDraft2Types.Array:
                outp_dict[outp_id] = Output(Optional[list])
            elif outp_type in CWLDraft2Types.String:
                outp_dict[outp_id] = Output(Optional[str])
            elif outp_type in CWLDraft2Types.Int:
                outp_dict[outp_id] = Output(Optional[int])
            elif outp_type in CWLDraft2Types.Bool:
                outp_dict[outp_id] = Output(Optional[bool])
            elif outp_type in CWLDraft2Types.Float:
                outp_dict[outp_id] = Output(Optional[float])
            elif "type" in outp_type:
                if outp_type["type"] == "enum":
                    outp_dict[outp_id] = Output(Optional[str])
                if outp_type["type"] == "array":
                    outp_dict[outp_id] = Output(Optional[list])
    else:
        logger.error(f"CWL version not recognised: {cwl_version}")
        raise Exception(f"CWL version not recognised: {cwl_version}")

    input_dict["app_"] = Input(sb.App, default=app)
    input_dict["project_"] = Input(sb.Project, default=project)
    subt = Step.new(
        inputs=input_dict, outputs=outp_dict, execute=execute_method, cls_name="RunApp"
    )
    return subt
