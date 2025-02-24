=========
ChangeLog
=========


2.1.37 (2024-05-23)
-------------------

Bug
~~~

- (Lineedit) Fix LineEdit duplicate textChanged signal overriding Qt builtin signal resulting in widget not updating correctly.


2.1.36 (2024-05-10)
-------------------

Bug
~~~

- (Buttonicons) Fix DPI scaling of buttons not applying.
- (Dialogs) Fix dialog and mainWindow widgets using obsolete .Desktop().
- (Extendedbutton) Removed clicked signal being overridden causing double the amount of events.
- (Lineedit) Fix silent recursion error in LineEdit using pyside2 which errors in PySide6.
- (Pyside6) Fix ButtonEnumerationDelegate failure under PySide6 using enum hints.
- (Pyside6) Fix DpiScaling not passing through args in __init__ for py3/pyside6 compatibility.
- (Pyside6) Fix dpiMult fail when not using maya.
- (Pyside6) Fix listviewPlus failure under PySide6 using enum.
- (Pyside6) LeafTreeFilterProxyModel fix use of obsolete method "modelIndex.child", which fixes a crash.
- (Pyside6) Fix TableViewExample failure under PySide6 using enum.
- (Screengrabber) Fix screengrabber using obsolete .Desktop().
- (Thumbnailwidget) Replace wheelEvent.pos with QCursor.pos to work between pyside versions.

Change
~~~~~~

- (Qt.Py) PySide6 compatibility updates for QDesktop and pixel capturing.
- (Qt.Py) PySide6 compatibility updates.


2.1.35 (2024-05-03)
-------------------

Bug
~~~

- (Frameless) Fix Frameless inheritance issue with python3 and pyside6.
- (Iconbuttons) Fix ButtonIcons inheritance issue with python3 and pyside6.

Change
~~~~~~

- (Compatibility) Switched out some uses of QRegExp for QRegularExpression for Pyside6 forward compatibility.
- (Pythonhighlighter) Replaced QRegExpr with QRegularExpression for forward compatibility reasons with pyside6.
- (Qregexpvalidator) Switched to using QRegularExpressionValidator when QT version <= "5.12.5" for compatibility with QT6.


2.1.34 (2024-02-21)
-------------------

Added
~~~~~

- (Icons) TreeView branch icons added.

Bug
~~~

- (Imageview) FileModel files extensions not working with mixedCase for OSX/linux.
- (Joinedradio) JoinedRadio buttonReleased replaced with buttonClicked because clicked handles ignoring the event if mouse position isn't on top of the buttons.
- (Stylesheet) Fix icon paths being set in stylesheet as a string instead of unicode.


2.1.33 (2024-01-22)
-------------------

Added
~~~~~

- (Delegates) Added LineEdit+button as an item delegate.
- (Lineeditbuttonwidget) Double click show and focus the internal LineEdit. lineEdit focusOutEvent hides the lineEdit.
- (Tableviewplus) Added selectedRowsIndices method to return QIndices for unique rows.

Bug
~~~

- (Imagemodel) OSX and Linux case sensitive issues with extensions.


2.1.32 (2023-12-05)
-------------------

Added
~~~~~

- (Joinedradio.Py) Added tooltips for the joined radio button. As used in the Hive UI.
- (Widgets.Py) Added tooltip for Zoo windows that displays the URL if one is given.


2.1.31 (2023-11-10)
-------------------

Bug
~~~

- (Combobox) Temporary fix to comboboxSearchable DPI issues where text would be clipped when OS DPI scale is above 100%.
- (Extendedbutton) Fix MouseClicked and release signals being emitted at the wrong time and stylesheets incorrectly being applied: thanks to Simon Leykamm for the fix.
- (Extendedbutton) Fix setMaximumHeight and setMaximumWidth calling wrong base method.

Change
~~~~~~

- (Elements) Added InputDialog class to elements.


2.1.30 (2023-10-05)
-------------------

Added
~~~~~

- (Pythoneditor) Add separate signal for newTabAdded which occurs after the tab was created.


2.1.29 (2023-09-27)
-------------------

Added
~~~~~

- (Logoutputwidget) Added Clear Text action to context menu.

Bug
~~~

- (Treeview) TreeView inability to not sort.


2.1.28 (2023-09-19)
-------------------

Bug
~~~

- (Sourcecodeeditor) Fix dedent hotkey not working.


2.1.27 (2023-08-11)
-------------------

Added
~~~~~

- (Uiconstants.Py) No icon button added spacing constant.

Bug
~~~

- (Lineedit) SetAlphanumericValidator not support 0-9 but only 1-9.


2.1.25 (2023-06-22)
-------------------

Added
~~~~~

- (Iconlib) Add support for passing qrc resource path.
- (Qtmodels) Added first iteration of the RootIndexProxyModel extension. BugFix -(TreeViewPlus) Fix Retrieving QModelIndexes not supporting multiple proxy models.
- (Uiconstants) Padding, btn icon size and default icon color constants added.
- (Joinedradio.Py) Button height can be changed on init.

Bug
~~~

- (Leftalignedbutton) LeftAlignedButton not using default icon color of 50% grey.
- (Qtreeview) Fix AttributeError raised when QApplication instance is core not GUI.
- (Uiconstants) Fix Incorrect way of retrieving doubleClickInterval.
- (Zoowindow) Fix eventFilter Return TypeError when host application closes.

Change
~~~~~~

- (Dialogs) Moved getDirectoriesDialog to dialogs.py.
- (Leftalignedbutton) Removed iconColor, iconSize arguments and replaced with only icon which takes the icon instance.
- (Leftalignedbutton) Replaced addMenuAction icon argument with icon instance.
- (Leftalignedbutton) Add iconColor override to leftAlignedButton.
- (Tooldata) Update old tooldata imports to use zoo.core version.


2.1.24 (2023-05-10)
-------------------

Bug
~~~

- (Imageview) Fix ZooSceneModel default thumbnail being empty resulting in no new thumbnail being saved.
- (Leftalignedbutton) LeftAlignedButton not using default icon color of 50% grey.
- (Qtreeview) Fix AttributeError raised when QApplication instance is core not GUI.
- (Uiconstants) Fix Incorrect way of retrieving doubleClickInterval.

Change
~~~~~~

- (Dialogs) Moved getDirectoriesDialog to dialogs.py.


2.1.23 (2023-05-03)
-------------------

Added
~~~~~

- (Buttons.Py) Added new buttons LeftAlignedButtonBase() and leftAlignedButton() which support both Maya resource icons and Zoo.
- (Buttons.Py) LeftAlignedButtonBase() added helper method for adding mouse click menu items.
- (Buttons.Py) LeftAlignedButton() Support for icon size override and transparent background for icon buttons.

Bug
~~~

- (Combobox) Combobox item sorting failing on byte strings.
- (Dpiscaling) Maya Custom Dpi scaling never gets retrieved.
- (Icondelegate) Error Occurs when an Item has no icon.
- (Keyboardmouse) Shift key wasn't support for normal keys.
- (Pathwidget) Opening explorer would always open at user home instead of provided path.
- (Sourcecodeinput) Fix Shift delete not being accepted.
- (Sourcecodeinput) Fix case where accepted hotkeys double up keyboard input.

Change
~~~~~~

- (Leftalignedbuttonbase) Support for rightClick/leftClick menu.
- (Pathwidget) PathWidget to allow default browserPath to be editable.
- (Buttons.Py) 4k fix to the new button leftAlignedButton().
- (Buttons.Py) LeftAlignedButton() now with more options and 4k issues fixed.

Removed
~~~~~~~

- (Utils) Moved strutils from zoo_core to core.


2.1.22 (2023-04-05)
-------------------

Added
~~~~~

- (Pythoneditor) Added basic support for adding/removing hotkeys.

Bug
~~~

- (Buttonround) Missing default values causing a TypeError.
- (Eventkeysequence) QKeyPressEvent Conversion to QKeySequence doesn't support shift and special characters.
- (Listviewplus) RegisterRowDataSource errors when when model isn't applied.
- (Pythoneditor) Fix isModified AttributeError.
- (Pythoneditor) Fix setLineWrapMode AttributeError.
- (Pythoneditor) Fix setModified AttributeError.
- (Startup) Fix startup file to avoid importing modules before they exist due to later zoo version logic.
- (Treeviewplus) SetAlternatingColorEnabled doesn't set the tree state only stylesheet.
- (Popups.Py) Fixed bug with the info icon not working for info boxes.

Change
~~~~~~

- (Core) ThreadedFunc to not print exception to avoid double output.
- (Inputdialog) Support for a third button.
- (Preferences) Updated all prefutils module imports with new namespace.
- (Qthreads) Added running flag to RunnableFunc.
- (Textedit) Support for retrieve the appropriate widget height from the current text.
- (Textedit) Support for setting document margins.


2.1.21 (2023-03-07)
-------------------

Bug
~~~

- (Eventkeysequence) Handle remapping special characters key presses.


2.1.20 (2023-03-02)
-------------------

Added
~~~~~

- (Datasources) Added support for setting tooltips via dataModel.
- (Datasources) Added support for setting value for custom role.
- (Hotkeydetectedit) Added support for all keyboard keys.Added support for customizing disabled keys.
- (Listmodel) Support iconSize role and custom roles.
- (Listviewplus.Py) Added methods for adjusting spacing of the elements with spacing/margins.

Bug
~~~

- (Comboboxregular) ComboBoxRegular is forced to not support middle mouse scroll, now provides the option.
- (Delegate) PixmapDelegate paint method always errors.
- (Listviewplus) Replace search widget with our zoo searchEdit.
- (Treeview) Shift expand not working.
- (Buttons.Py) Fixed btnSize keyword argument error regarding a simple typo.

Change
~~~~~~

- (Checkbox) Checkbox widget to allow label as a kwarg.
- (Slidingwidget) SlidingWidget to supportActiveState.


2.1.19 (2023-01-25)
-------------------

Bug
~~~

- (Combobox) Fix Combobox wheel event causing a scroll when combobox popup has not shown.
- (Directorypopup) Adding a category to a folder will now search parents for a valid parent or use the root.
- (Popups.Py) Fixed 4k double sized popup windows (base).

Change
~~~~~~

- (License) Update copyright for 2023.


2.1.18 (2022-12-03)
-------------------

Bug
~~~

- (Qt) Fix QT depreciated methods for treeItem for better interoperability.
- (Qt) Fix Layouts having the same parent causing Qt logs to be output of linux/OSX.


2.1.17 (2022-11-17)
-------------------

Bug
~~~

- (Crash) Crash during on wheelEvent in ThumbnailWidget due to using missing method delta() with PyQt5.
- (Crash) Crash during on wheelEvent in comboeditwidget due to using missing method delta() with PyQt5.
- (Crash) Crash during on wheelEvent in graphicsview due to using missing method delta() with PyQt5.
- (Crash) Crash during on wheelEvent in inputTextWidth due to using missing method delta() with PyQt5.
- (Crash) Crash during on wheelEvent in logoutput due to using missing method delta() with PyQt5.
- (Crash) Crash when adding item with no data to ComboEditWidget with PyQt.
- (Crash) Crash when creating ComboStandardItem with PyQt.
- (Crash) Fix crash in Combobox when using PyQt5.
- (Crash) Fix crash in Slider widget when using PyQt5.
- (Crash) Fix crash in imageView when using PyQt5.
- (Delegates) Fix error when drawing text with html.

Misc
~~~~

- (Docs) DocString fixes.


2.1.16 (2022-11-16)
-------------------

Bug
~~~

- (Qt) Fix Pyqt5 compatibility issues.


2.1.15 (2022-11-15)
-------------------

Bug
~~~

- (Qt) Fix wrapInstance usages not support PyQt.


2.1.14 (2022-10-26)
-------------------

Added
~~~~~

- (Minibrowser) Added hotkey "f" to focus to current selection.
- (Minibrowser) Helper method to add a new item from a file path to avoid full refreshes.

Bug
~~~

- (Delegates) Fix comboboxButton delegate being incorrect width.
- (Graphicpath) Fix setting setCurveType not triggering update event.
- (Graphicsview) Fix context menu still triggering qt default menu.
- (Minibrowser) Update a thumbnail updates wrong item when filtering by renderer.
- (Minibrowser) Renaming item doesn't refresh thumbnails correctly.
- (Minibrowser) Saving and new or replacing a thumbnail no longer requires a full refresh resulting in a more responsive UI.
- (Minibrowsers) Initial zoom and resize fixes.
- (Zoowindow) Displaying a window may show offscreen.

Change
~~~~~~

- (Mainwindow) Default saveWindowPref to off which was effecting offscreen positioning.
- (Minibrowser) Ignore selection when zooming if the selection is not visible.
- (Minibrowsers) Removed Redundant item model arguments.
- (Snapshotui) SnapshotUI no longer is responsible for saving only creating a QPixmap of the Rect. Resulting in a more robust widget and client code no longer needs it to keep the save path in sync. Save location and logic is now the clients' responsibility.
- (Zoowindow) Removed show argument from init function due to visual artifacts it can cause due to events.
- (Zoowindow) Support for provide custom window settings location.
- (Zoowindow) Stash the default window flags.


2.1.13 (2022-09-29)
-------------------

Bug
~~~

- (Browsers) Browsers memory usage heavily reduced, removed redundant image copy, all images are now scaled down if needed to maximum size of 512x512.
- (Imageview) Crash in Maya2018 when loading images.
- (Minibrowsers) Fix AttributeError raised during resize event.
- (Mouseslider) Ontick fails due to TypeError.
- (Treeview) Fix right click context menu not show up unless double right-clicked.
- (Elements) Fix cyclic imports to elements.

Change
~~~~~~

- (Minibrowsers) Delay connections bindings until all widgets are initialized.
- (Treeview) TreeView base class to support double-clicked signal.
- (Treeviewplus) Change search widget to use the slidingWidget.
- (Treeviewplus) TreeViewPlus search to be a sliding widget.
- (Combobox) Combobox setToText to support match flags.

Removed
~~~~~~~

- (Browsers) Removed unused methods from data model.


2.1.12 (2022-07-25)
-------------------

Bug
~~~

- (Browsers) Constant flicker occurred during zoom.
- (Browsers) Extra fixes to zooming and resizing.
- (Browsers) Loading thumbnail doesn't update the format ext. Resulting in a mismatch ext/format when saving.
- (Browsers) Refresh only loading a fixed amount of images instead of whats visible. Also reduced refresh calls.

Misc
~~~~

- (Popups.Py) FileDialog_directory works if no parent is passed in.


2.1.11 (2022-07-20)
-------------------

Added
~~~~~

- (Infoembedwindow.Py) Added support for loading zooInfo files that do not have standard metadata keys. Now blank keys are created if they are missing.
- (Modelutils) Added ProxyModel utilities functions for retrieving root model and indices.

Bug
~~~

- (Browsers) Avoid attempting to Resize images if the requested size is 0.
- (Browsers) Crash when accessing Shared image data when Image thread is writing.
- (Browsers) Inconsistent Crash when accessing the items model after the image loaded thread update signal.
- (Browsers) Incorrect implementation for scrollTo when leaving the view led to focusing on the wrong item index, Solution was to remove custom replementation and rely on QT core.
- (Browsers) Probable Fix to crash when new items were added to the model.
- (Browsers) Searching browser results doesn't load required images.
- (Browsers) Small improvement to item scaling.
- (Browsers) The number of Items Displayed doesn't take the initial size of the view into account.
- (Browsers) TypeError raised during wheelevent.
- (Colors) HsvColor func raises AttributeError.
- (Combobox) Specifying the combobox to be sorted by default results in AttributeError being raised.
- (Listmodel) List model not working in any way.
- (Listview) List view not working in any way.
- (Logging) Fix logging QMenu AttributeError for python packages.
- (Minibrowser) Fixed threaded image loading never happening, Removes workaround code.
- (Minibrowser) Incorrect model filtering logic results in incorrect index queries and visual bugs. Replaced with QSortFilterProxyModel.
- (Okcanceldialog) Fix "layout" name conflict with QTs layout function name.
- (Renderermixin) Renderer filter incorrectly sets data model filter.
- (Stringedit) Fix "layout" name conflict with QTs layout function name.
- (Syntaxhighlighting) Fix SyntaxError when importing the hightlighter module on py2 due to UTF-8 encoding not being used.

Change
~~~~~~

- (Browsers) Image Resizing to always take vertical scrollbar into account to have more consistent column count.
- (Browsers) Scroll sensitivity setting.
- (Browsers) Scroll sensitivity setting.
- (Combobox) AddItem to support passing userData.
- (Flowtoolbar) Faster calculation of tools.
- (Minibrowser) Light code cleanup.
- (Minibrowser) Remove constant initialization of a new font instance per item draw.
- (Pathwidget) Support providing a label.

Misc
~~~~

- (Assorted) Doc strings fixed to be sphinx compatible. Added ( assorted ) Assorted doc strings added and tweaked.
- (Minibrowser.Py) Small doc change.
- (Thumbnailwidget.Py) Changed browser scroll bar slider sensitivity to 5.

Remove
~~~~~~

- (Examples) Removed thumbnailview example which is no longer possible without toolsets.
- (Filemodel) Removed Redundant FileModel module.


2.1.10 (2022-05-31)
-------------------

Added
~~~~~

- (Elements) Added IconLabel widget Class.
- (Elements) Added IconLabel widget Class.
- (Pythoneditor) Support block indentation basics.
- (Pythoneditor) Support for block comments.
- (Pythoneditor) Support for insert new line with shift+return.
- (Sourcecodeeditor) Added support for brace surrounding of selected text.
- (Syntaxhighlighter) Support Function name for highlighting.
- (Utils) Added blockSignalsContext() context manager to temporarily block Qt Signals on a list of QObjects.

Bug
~~~

- (Comboeditwidget) LineEdit now clears focus instead of disabling the widget to allow better stylesheet and expected colors.
- (Datasources) Enumeration current index doesn't reset if the when setting enum list and the current value doesn't exist.
- (Datasources) Enumeration setData and data never setting current value.
- (Datasources) Item text colors not inline with stylesheets.
- (Datasources) Setting Enumeration values resets all column indexes.
- (Datasources) TypeError occurs when sorting userObjects.
- (Delegate) EnumerateButton doesn't take ItemIsEditable flag into account.
- (Delegates) Enumeration Delegate doesn't take ItemIsEditable flag into account.
- (Delegates) Html Delegate painter not using handling dataSource text color state.
- (Directorypopup) Opening the directory popup would not reset position alongside toolset.
- (Imageview) Incorrect arguments passed to dataChanged.emit which raises an error.
- (Lineedit) Forced stylesheet override on lineEdit caused incorrect style depending on state.
- (Logoutput) Logging an error would result in a html syntax error instead.
- (Shaderpresets.Py) Select the shader now selects the shader in component mode.
- (Sourcecodeeditor) InputTextWidget new line fails to move text to next line.
- (Sourcecodeeditor) Number line width not updating based on number width.
- (Sourcecodeeditor) NumberBar doesn't scale when zooming editor.
- (Stylesheet) Fix stylesheet skipping certain values during parsing resulting in incorrect css.
- (Tabwidget) Replace TabWidget add button with Ctrl+T hotkey.

Change
~~~~~~

- (Combobox) Removed redundant stylesheet call.
- (Hboxlayout) Allow passing margins and spacing as arguments.
- (Hboxlayout) Allow passing margins and spacing as arguments.
- (Logoutput) Colours take into account the background color.
- (Minibrowsers) Moved pathList widget from preferences repo to minibrowser package to remove cross dependencies.
- (Numberbar) Better handling of updating on events.
- (Pythoneditor) Moved into sub package "sourcecodeeditor".
- (Sourcecodeeditor) Split modules apart for widgets.
- (Sourcecodeeditor) Support surround with string.
- (Sourcecodeeditor) Updated source code syntax highlighting.
- (Stylesheet) Updated extended button menus to inherent stylesheet from zoo.
- (Syntaxhighlighter) Better coloring and fixing numbers within strings being incorrectly highlighted.
- (Syntaxhighlighter) Refactored syntax highlighter theme and keyword data structures so we can support multiple languages and themes.
- (Tabwidget) "Tab add", "remove", "close other" added.
- (Tabwidget) RenameTab to use zoo input dialog.

Remove
~~~~~~

- (Documentation) Fix failed documentation parser.

Removed
~~~~~~~

- (Sourcecodeeditor) Code execution from python editor to allow higher level control.


2.1.9 (2022-04-16)
------------------

Added
~~~~~

- (Delegates) Added combobox with a button, purpose built for updates from a selection.
- (Itemviews) HtmlDelegate with text margin supprts.
- (Tablemodel) Support set updating enumeration list via model.setData.

Bug
~~~

- (Core) Incorrect function call for determining maya mode.
- (Datasources) Incorrect default mimeData type.
- (Extendedbutton) Fix ExtendedButton menus not having a parent widget.
- (Frameless) Resizer widgets to localized cursors instead of application wide to avoid overriding maya.
- (Itemviews) Change column visibility results in typeError.
- (Tablemodel) Flags method doesn't support drop on root index.
- (Tableview) Fix case where changing cell value changes all column cells resulting in errors.
- (Tabwidget) Fix tabwidget context menu AttributeError.
- (Viewsearchwidget) Height of search widget not matching other widgets.
- (Zoowindow) Minimize and maximize buttons not working.

Change
~~~~~~

- (Combobox) Support setting the label from the text not the data.
- (Datasources) Default setUserObjects to the current children objects.
- (Datasources) Enumeration DataSources now handle data,setData,setEnums, enums caching by default.
- (Directorypopup) Folder tooltips to show filesystem path.
- (Docs) General fixes to documentation errors.
- (Examples) Updated pyqt example tableview to use latest changes.
- (Frameless) Frameless resizers continued removal of overriding QApplication cursor instead using localized widget.setCursor.
- (Tablemodel) Better support for drag and drop.
- (Tablemodel) RowCount method to default parent Index to root.
- (Tablemodel) Support moveRows.
- (Tableview) Optional manual reload flag.
- (Tableview) Support for retrieving selected items and indexes.
- (Tableviewplus) Change tableview variable to TableView for consistency.
- (Treemodel) Reuse role constants from tablemodel.
- (Treemodel) Support for enumeration data role.


2.1.8 (2022-03-14)
------------------

Added
~~~~~

- (Minibrowser) Support for categories.

Bug
~~~

- (Core) Fix specific use of ntpath instead use os.path.
- (Datasources) IsRoot returns a False positive.
- (Directorypopup) Selection change event to correctly retrieve directory ids.
- (Minibrowser) After Snapshot New occurs any selection afterwards will result in a popup per item.
- (Minibrowser) Ensure preferences are updated when there's no active selection.
- (Minibrowser) Save Popup button label to be Set Directory not paste.
- (Minibrowser) Snapshot popup should only display selected directories if there is any.
- (Minibrowser) When theres no active directory but only 1 user directory don't show the directory popup just use the first directory.
- (Minibrowsers) Thumbnail won't save if the the save directory doesn't exist.
- (Screengrab) AttributeError raised when QApplication.instance() isn't a QApplication instance but QCoreApplication.
- (Treemodel) Copy action when dragging and dropping results in incorrect deletion.
- (Treemodel) Incorrect indices being removed. better handling of index overflow.
- (Treemodel) TypeError when handling drag and drop.
- (Treeview) SelectionEvent not handling proxyModel conversion.
- (Treeviewplus) Dynamic sorting not working.
- (Treeviewplus) Incorrectly sorting order.
- (Treeviewplus) Selection retrieve not converting proxy filter indices, resulting in crashes and misaligned indices.

Change
~~~~~~

- (Datasources) Base class now handles removing children.
- (Minibowser) SnapShot replace to use current viewer selection.
- (Minibrowser) Saving a new thumbnail will remember previous location. Will reuse only if the current selection is the same as the previous.
- (Treeview) Support tree traversal with dataSources.


2.1.7 (2022-02-22)
------------------

Added
~~~~~

- (Virtualslider) Add virtual slider to minibrowser.
- (Virtualslider.Py) Thumbnail Sliders always emit in both directions regardless of the initial movement.

Bug
~~~

- (Browsers) Fix suffixFilter model not handling empty suffix .
- (Minibrowser Search) Fix issues relating to search.
- (Treemodel) Inserting a row outside the parent row count results in a crash or double up of items.
- (Virtualslider) Issue for 2020 scrolling.

Change
~~~~~~

- (Doc) Add minor docs to search widget.
- (Doc) Documentation for thumbnailwidget.
- (Doc) Move virtual slider documentation to under class header.
- (Mayascenes) Move maya scenes thumbnail into filedependencies folder.
- (Virtualslider) Extra Docs and switch to ints instead.


2.1.6 (2022-02-04)
------------------

Added
~~~~~

- (Collapsableframethin) New widget plus extra changes.
- (Joinedradiobutton) Return index of button, set checked by index.
- (Messagebox) Add messagebox that can take custom widgets.
- (Path Widget) Tooltips can now be set on elements.PathWidget().
- (Pathwidget) Added new file path saving widget.
- (Pathwidget) Support for both open and save path widgets.
- (Treemodel) Support for lazy loading.

Bug
~~~

- (Checkbox.Py) Fix issue clicking checkbox would error.
- (Combobx) Fix for toolTips not showing if no label on the combobox.
- (Core) Path widget to support search filters in dialog popup.
- (Datasources) Fix model instance being none when adding child sources.
- (Itemmodel) Fix IndexError edge case when the item count isn't in sync with the model.
- (Listview) Right-clicking in the view produced an empty context menu.
- (Minibrowser) Ensure the preferences interface isn't loaded until a single instance is loaded.
- (Toolsets) Include False in toolset skipChildren check.

Change
~~~~~~

- (Code) Add some documentation.
- (Directorypopup) Replace addDirectory pop up with standard Qt dialog.
- (Divider) Move styling to QSS, add dpi scaling.
- (Doc) Added documentation and clean up for ContainerWidgets.
- (Messagebox) Use zoo message boxes instead of qt.
- (Pathwidget) To use textModified signal instead of editingFinished.
- (Savedialog) Allow for parent instance to be passed.
- (Treeviewplus) Context menu to use root node.


2.1.5 (2022-01-18)
------------------

Added
~~~~~

- (Comboeditwidget) Added setLabel method to ComboEditWidget().
- (Docs) Added initial documentation rst.

Bug
~~~

- (Extendedbutton) Anything other than LeftButton click would fail to run.

Change
~~~~~~

- (Groupedtreewidget) Extra code to get tree size update more reliable.


2.1.4 (2021-12-18)
------------------

Added
~~~~~

- (Color Picker) New Colour Picker and Joined Radio Widget.
- (Groupedtreewidget) Support enabling or disabling drag and drop.

Bug
~~~

- (Colorpopup) Remove py3 syntax.


2.1.3 (2021-12-08)
------------------

Added
~~~~~

- (Extended Button) Insert Separator by index for extended button.
- (Logging) Additional debug logs.
- (Mini Browsers) Add extra debug logs for minibrowsers.

Bug
~~~

- (Qicons) Fix QIcons being initialized before a QApplication maya exist.
- (Stand Alone) Center zoo window correctly in standalone windows.

Change
~~~~~~

- (Background Color) Allow alpha values in background color.
- (Color Button) Temporarily disable color button.
- (Frame Shadow) Set shadow effect on the frame instead to avoid QT warning.
- (Thumbnails) Load png as thumbnails.png workaround.
