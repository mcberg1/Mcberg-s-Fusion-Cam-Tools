import adsk.core
import adsk.fusion
import os
from ...lib import fusion360utils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface
import adsk.core, adsk.fusion, adsk.cam, traceback, os
import sys
# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdSPP'
CMD_NAME = 'Smart Post Process'
CMD_Description = 'Post process with a few helpful options'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = config.workspace
PANEL_ID = config.panel_id
PANEL_NAME = config.panel_name
TAB_ID = config.tab_id
TAB_NAME = ''
COMMAND_BESIDE_ID = ''



# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get target toolbar tab for the command and create the tab if necessary.
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)

    if toolbar_tab is None:
        toolbar_tab = workspace.toolbarTabs.add(TAB_ID, TAB_NAME)

    # Get the panel the button will be created in.
    panel = toolbar_tab.toolbarPanels.itemById(PANEL_ID)
    if panel is None:
        panel = toolbar_tab.toolbarPanels.add(PANEL_ID, PANEL_NAME, '', False)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    toolbar_tab = workspace.toolbarTabs.itemById(TAB_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

    # Delete the panel if it is empty
    if panel.controls.count == 0:
        panel.deleteMe()

    # Delete the tab if it is empty
    if toolbar_tab.toolbarPanels.count == 0:
        toolbar_tab.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # TODO Define the dialog for your command by adding different inputs to the command.

    # Create a simple text box input.
    #inputs.addTextBoxCommandInput('text_box', 'Some Text', 'Enter some text.', 1, False)



    separate_drills = inputs.addBoolValueInput('separate_drills', 'Separate Drills', True, '', False)
    separate_drills.tooltip = "When checked, operations with tool #1 will be exported as individual GCode files,\n and all other operations will be exported in the same file like normal. \nPrimarily for separating drill programs, so bits can be swapped, \nthis works for any operation with tool number 1"
    
    drop_down_style = adsk.core.DropDownStyles.LabeledIconDropDownStyle
    post_processor_input = inputs.addDropDownCommandInput('post_processor', 'Post Processor', drop_down_style)
    post_processor_input_items = post_processor_input.listItems
    post_processor_input_items.add('Tormach', True)
    post_processor_input_items.add('Green Machine (Fanuc)', False)



    # Create a value input field and set the default using 1 unit of the default length unit.
    #defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    #default_value = adsk.core.ValueInput.createByString('1')
    #inputs.addValueInput('value_input', 'Some Value', defaultLengthUnits, default_value)

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    #futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    # TODO ******************************** Your code here ********************************

    # Get a reference to your command's inputs.
    
    inputs = args.command.commandInputs
    sd: adsk.core.BoolValueCommandInput = inputs.itemById('separate_drills')
    pp: adsk.core.DropDownCommandInput = inputs.itemById('post_processor')

    # Do something interesting
    separate = sd.value
    post = pp.selectedItem.index
    #msg = f'Separate Drills: {text}<br>Post Processor: {"tormach" if expression == 0 else "fanuc"}'
    exportCam(separate, post)
    #ui.messageBox(msg)




# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs
    
    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    valueInput = inputs.itemById('value_input')
    if valueInput.value >= 0:
        inputs.areInputsValid = True
    else:
        inputs.areInputsValid = False
        

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []



def exportCam(separate, post):
    #if post == 1: #its fanuc, and wants numerical filenames
    fileNumber = 0000

    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        doc = app.activeDocument
        products = doc.products
        product = products.itemByProductType('CAMProductType')

        # check if the document has a CAMProductType.  I will not if there are no CAM operations in it.
        if product == None:
            ui.messageBox('There are no CAM operations in the active document.  This script requires the active document to contain at least one CAM operation.',
                            'No CAM Operations Exist',
                            adsk.core.MessageBoxButtonTypes.OKButtonType,
                            adsk.core.MessageBoxIconTypes.CriticalIconType)
            return

        cam = adsk.cam.CAM.cast(product)

        # specify the program name, post configuration to use and a folder destination for the nc file
        fD = ui.createFolderDialog()
        fD.title = "Post Location:"
        dResult = fD.showDialog()
        if dResult == adsk.core.DialogResults.DialogOK:
            outputFolder = fD.folder
            ui.messageBox('Exporting To: {}'.format(fD.folder))
        else:
            ui.messageBox('Invalid Folder!')
            #quit()
            sys.exit(1)
            
        

        # set the post configuration to use based on Operation Type of the first Setup
        firstSetupOperationType = cam.setups.item(0).operationType
        if firstSetupOperationType == adsk.cam.OperationTypes.MillingOperation:
            postConfig = os.path.join("", config.post_paths[post])
        else:
            ui.messageBox("bruh")


        # specify the NC file output units
        #units = adsk.cam.PostOutputUnitOptions.DocumentUnitsOutput
        units = adsk.cam.PostOutputUnitOptions.InchesOutput
#        units = adsk.cam.PostOutputUnitOptions.MillimetersOutput

        # create the postInput object
        
        postInput = adsk.cam.PostProcessInput.create('DEFAULT NAME', postConfig, outputFolder, units)
        postInput.isOpenInEditor = False
        
        # create the post properties
        postProperties = adsk.core.NamedValues.create()
        # create the disable sequence number property
        disableSequenceNumbers = adsk.core.ValueInput.createByBoolean(False)
        postProperties.add("showSequenceNumbers", disableSequenceNumbers)
        # add the post properties to the post process input
        postInput.postProperties = postProperties
        
        
        
        # set the value of scenario to 1, 2 or 3 to post all, post the first setup, or post only the first operation of the first setup.
       
        #ui.messageBox('The first Toolpath in the first Setup will be posted')

        separate_drills = bool(separate)
        ops = adsk.core.ObjectCollection.create()
        for s in cam.setups:
            fileNumber -= (fileNumber)%1000 
            fileNumber += 1000
            #ui.messageBox(str(s.allOperations.objectType))
            #for f in s.folders:
            for o in s.allOperations:
                        if o.hasToolpath == True:
                            if o.parameters.itemByName('tool_number').expression == "1" and separate_drills:
                                fileNumber += 1
                                toolName = o.parameters.itemByName('tool_description').expression.replace("/", "-").replace("\\", "-").replace("\"", "in").replace("'", "")
                                fileName = o.name + " " + toolName
                                if post == 1: #fanuce, wants numerical filenames
                                    fileName = str(fileNumber)
                                postInput = adsk.cam.PostProcessInput.create(fileName, postConfig, outputFolder + "\\" + s.name, units)
                                #ui.messageBox(o.strategy + ", " + str(o.strategyType)) #stratType 22 is drilling
                                postInput.postProperties = postProperties
                                postInput.isOpenInEditor = False
                                cam.postProcess(o, postInput)
                            else:
                                ops.add(o)
            if ops.count != 0:
                    fileNumber += 1
                    fileName = s.name
                    if post == 1: #fanuce, wants numerical filenames
                        fileName = str(fileNumber)
                    postInput = adsk.cam.PostProcessInput.create(fileName, postConfig, outputFolder + "\\" + s.name, units)
                    postInput.postProperties = postProperties
                    postInput.isOpenInEditor = False
                    cam.postProcess(ops, postInput)


                        
            
           # setup = setups.item(0)
           # operations = setup.allOperations
           # operation = operations.item(0)
           # if operation.hasToolpath == True:
           #     cam.postProcess(operation, postInput)
           # else:
           #    ui.messageBox('Operation has no toolpath to post')
           #    return

        ui.messageBox('Post processing is complete. The results have been written to:\n"' + outputFolder)

        # open the output folder in Finder on Mac or in Explorer on Windows
        if (os.name == 'posix'):
            os.system('open "%s"' % outputFolder)
        elif (os.name == 'nt'):
            os.startfile(outputFolder)
    except SystemExit as e:
        sys.exit(e)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))