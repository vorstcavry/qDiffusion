import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

Rectangle {
    id: root

    property alias text: textArea.text
    property alias font: textArea.font
    property alias monospace: textArea.monospace
    property alias readOnly: textArea.readOnly
    property alias area: textArea
    property alias scrollBar: controlScrollBar

    onActiveFocusChanged: {
        if(root.activeFocus) {
            textArea.forceActiveFocus()
        }
    }

    function completeText(text, start, end) {
        textArea.remove(start, end)
        textArea.insert(start, text)
    }
    
    signal tab()
    signal input(int key)
    signal release(int key)
    signal menu(int dir)
    property var menuActive: false

    color: "transparent"

    SContextMenu {
        id: contextMenu
        SContextMenuItem {
            text: "Cut"
            onPressed: {
                textArea.cut()
            }
        }
        SContextMenuItem {
            text: "Copy"
            onPressed: {
                textArea.copy()
            }
        }
        SContextMenuItem {
            text: "Paste"
            onPressed: {
                textArea.paste()
            }
        }
    }

    Flickable {
        id: control
        anchors.fill: parent
        contentHeight: textArea.height
        contentWidth: width
        boundsBehavior: Flickable.StopAtBounds
        clip: true
        interactive: false

        ScrollBar.vertical: SScrollBarV {
            id: controlScrollBar
            parent: control
            anchors.top: control.top
            anchors.right: control.right
            anchors.bottom: control.bottom
            policy: control.height >= control.contentHeight ? ScrollBar.AlwaysOff : ScrollBar.AlwaysOn
            stepSize: 1/Math.ceil(textArea.contentHeight/textArea.font.pixelSize)
        }

        TextArea {
            id: textArea
            width: parent.width
            height: Math.max(contentHeight+10, root.height)
            padding: 5
            leftPadding: 5
            rightPadding: 10
            wrapMode: TextArea.Wrap
            selectByMouse: true
            persistentSelection: true
            FontLoader {
                source: "qrc:/fonts/Cantarell-Regular.ttf"
            }
            FontLoader {
                source: "qrc:/fonts/SourceCodePro-Regular.ttf"
            }

            property var monospace: false
            font.family: monospace ? "Source Code Pro" : "Cantarell"
            font.pointSize: 10.8
            color: COMMON.fg1

            onCursorRectangleChanged: {
                var y = cursorRectangle.y
                if(y < control.contentY + 5) {
                    control.contentY = y - 5
                }
                if(y >= control.contentY + control.height - 5) {
                    control.contentY = y - control.height + cursorRectangle.height + 5
                }
            }

            function weightText(inc) {
                var start = textArea.selectionStart
                var end = textArea.selectionEnd
                var text = textArea.text

                if (start == end || textArea.readOnly) {
                    return
                }

                if (text[start-1] != '(' && text[end] != ':') {
                    textArea.text = text.slice(0, start) + "(" + text.slice(start, end) + ":" + (1 + inc) + ")" + text.slice(end)
                    textArea.select(start+1, end+1)
                } else {
                    var trail = text.slice(end+1)
                    var idx = trail.indexOf(')')
                    
                    var weight = parseFloat(trail.slice(0,idx))
                    if (weight + inc < 0 && inc < 0) {
                        return
                    }

                    weight = (weight + inc).toFixed(1)
                    if (weight == "1.0" || weight == "NaN") {
                        textArea.text = text.slice(0, start-1) + text.slice(start, end) + trail.slice(idx+1)
                        textArea.select(start-1, end-1)
                    } else {
                        textArea.text = text.slice(0, start) + text.slice(start, end) + ":" + weight + ")" + trail.slice(idx+1)
                        textArea.select(start, end)
                    }
                }
            }

            Keys.onPressed: {
                event.accepted = true
                if(event.modifiers & Qt.ControlModifier && event.modifiers & Qt.ShiftModifier ) {
                    switch(event.key) {
                    case Qt.Key_Up:
                        weightText(0.1)
                        break
                    case Qt.Key_Down:
                        weightText(-0.1)
                        break
                    default:
                        event.accepted = false
                        break;
                    }
                } else {
                    switch(event.key) {
                    case Qt.Key_Tab:
                        root.tab()
                        break;
                    case Qt.Key_Return:
                        if(root.menuActive) {
                            root.tab()
                        } else {
                            event.accepted = false
                        }
                        break;
                    case Qt.Key_Escape:
                        if(root.menuActive) {
                            root.menu(0)
                        } else {
                            event.accepted = false
                        }
                        break;
                    case Qt.Key_Up:
                        if(root.menuActive) {
                            root.menu(1)
                        } else {
                            event.accepted = false
                        }
                        break;
                    case Qt.Key_Down:
                        if(root.menuActive) {
                            root.menu(-1)
                        } else {
                            event.accepted = false
                        }
                        break;
                    default:
                        event.accepted = false
                        break;
                    }
                }
                
                if(!event.accepted) {
                    root.input(event.key)
                }
            }

            Keys.onReleased: {
                root.release(event.key)
            }
        }

        MouseArea {
            anchors.fill: textArea
            acceptedButtons: Qt.RightButton
            onPressed: {
                contextMenu.popup()
            }
            onWheel: {
                if(wheel.angleDelta.y < 0) {
                    scrollBar.increase()
                } else {
                    scrollBar.decrease()
                }
            }
        }

        Keys.onPressed: {
            event.accepted = true
        }
    }
}