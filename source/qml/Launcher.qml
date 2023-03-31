import QtQuick 2.15
import QtQuick.Controls 2.15

import gui 1.0

ApplicationWindow {
    id: root
    visible: true
    width: 1100
    height: 600
    color: "#1a1a1a"
    title: "qDiffusion"

    Image {
        opacity: 0.5
        id: spinner
        source: "file:source/qml/icons/loading.svg"
        width: 80
        height: 80
        sourceSize: Qt.size(width, height)
        anchors.centerIn: parent
        smooth:true
        antialiasing: true   
    }

    RotationAnimator {
        target: spinner
        from: 0
        to: 360
        duration: 1000
        running: true
    }

    Component.onCompleted: {
        COORDINATOR.load()
    }

    Connections {
        target: COORDINATOR
        function onReady() {
            var component = Qt.createComponent("qrc:/Main.qml")
            if(component.status != Component.Ready) {
                console.log("ERROR", component.errorString())
            } else {
                component.createObject(root)
            }
        }
    }
}