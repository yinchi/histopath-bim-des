# Model Configuration

Parameters for the simulation module are encoded in a {py:class}`.Config` object. The
Entity Relationship Diagram for the {py:class}`.Config` class is shown below (click for full size):

![erd](_static/Config.erd.png){w=300px align=center}

Configurations can be parsed from an Excel worksheet using {py:meth}`.Config.from_workbook`. Example
worksheets are available in the `/assets` directory of the project, with prefixes `config_`.

## Generating a runner times configuration 

To specify a runner times configuration setting for {py:meth}`.Config.from_workbook`, an
Excel worksheet titled "Runner Times output" is required. An example Python script to generate
this file is:

```py
model = BimModel.from_ifc('../assets/private/histo.ifc')
runner_cfg_path = '../assets/histo.xlsx'  # base scenario, contains a single sheet "Runner Times"
cfg = RunnerConfig.from_excel(openpyxl.load_workbook(runner_cfg_path, data_only=True))
rt = runner_times(model, cfg)
excel.write_table(df, runner_cfg_path, 'Runner Times output', 'tableRunnerTimes')
```

The "Runner Times" and "Runner Times output" worksheets can then be pasted into a full configuration
file.
