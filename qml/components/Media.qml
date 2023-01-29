import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

Rectangle {
    id: view
    property string source
    property int sourceWidth
    property int sourceHeight
    property var scale: 1.0

    signal contextMenu()

    clip: true

    property var current: full.visible ? full : view

    CenteredImage {
        id: thumb
        visible: full.status != Image.Ready 
        source: (GUI.isCached(view.source) ? "image://sync/" : "image://async/") + view.source
        anchors.centerIn: view
        maxWidth: Math.min(current.width, view.sourceWidth)
        maxHeight: Math.min(current.height, view.sourceHeight)
        sourceWidth: view.sourceWidth
        sourceHeight: view.sourceHeight
        cache: false
        fill: true
    }

    CenteredImage {
        id: full
        anchors.centerIn: view
        asynchronous: true
        source: thumb.status != Image.Ready ? "" : "file:///"  + view.source
        visible: full.status == Image.Ready && thumb.status == Image.Ready
        smooth: view.sourceWidth*2 < width && view.sourceHeight*2 < height ? false : true
        maxWidth: Math.min(view.width, view.sourceWidth)
        maxHeight: Math.min(view.height, view.sourceHeight)
        sourceWidth: view.sourceWidth
        sourceHeight: view.sourceHeight
        fill: true
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.MiddleButton

        property var startX: 0
        property var startY: 0
        property var posX: 0
        property var posY: 0
        property var dragging: false

        onPressed: {
            posX = current.x
            posY = current.y
            startX = mouseX
            startY = mouseY
            dragging = true
        }

        onReleased: {
            dragging = false
        }

        onPositionChanged: {
            if(dragging) {
                current.anchors.centerIn = undefined

                current.x = posX + (mouseX - startX)
                current.y = posY + (mouseY - startY)

                bound()
            }
        }

        function bound() {
            var dx = (current.maxWidth - current.width)/2
            var dy = (current.maxHeight - current.height)/2

            var x = current.x + dx
            var y = current.y + dy
            var w = current.width
            var h = current.height

            if(x + w - dx < view.width/2)
                x = view.width/2 - w + dx
            if(y + h - dy < view.height/2)
                y = view.height/2 - h + dy

            if(x > view.width/2 + dx)
                x = view.width/2 + dx

            if(y > view.height/2 + dy)
                y = view.height/2 + dy

            current.x = x - dx
            current.y = y - dy
        }

        function scale(cx, cy, d) {
            current.anchors.centerIn = undefined

            d = view.scale * d

            var f = ((view.scale + d)/view.scale) -1

            if(view.scale + d < 0.1) {
                return
            }

            view.scale += d

            current.maxWidth = view.scale * Math.min(view.width, view.sourceWidth)
            current.maxHeight = view.scale * Math.min(view.height, view.sourceHeight)

            var dx = f*(cx - current.x)
            var dy = f*(cy - current.y)

            current.x -= dx
            current.y -= dy
            posX -= dx
            posY -= dy

            bound()
        }

        onWheel: {
            if(wheel.angleDelta.y < 0) {
                wheel.accepted = true
                scale(wheel.x, wheel.y, -0.1)
            } else {
                wheel.accepted = true
                scale(wheel.x, wheel.y, 0.1)
            }
        }
    }

    onSourceChanged: {
        reset()
    }

    onSourceHeightChanged: {
        reset()
    }

    onSourceWidthChanged: {
        reset()
    }

    onWidthChanged: {
        reset()
    }

    onHeightChanged: {
        reset()
    }

    function reset() {
        view.scale = 1
        full.anchors.centerIn = thumb
        full.maxWidth = Math.min(view.width, view.sourceWidth)
        full.maxHeight = Math.min(view.height, view.sourceHeight)
    }

    MouseArea {
        id: mouse
        anchors.fill: current
        hoverEnabled: false

        acceptedButtons: Qt.RightButton

        drag.target: thumb

        onClicked: {
            switch(mouse.button) {
            case Qt.RightButton:
                contextMenu()
                break;
            default:
                mouse.accepted = false
                break;
            }
        }
    }

    Drag.hotSpot.x: x
    Drag.hotSpot.y: y
    Drag.dragType: Drag.Automatic
    Drag.mimeData: { "text/uri-list": "file:///" + source }
    Drag.active: mouse.drag.active
}