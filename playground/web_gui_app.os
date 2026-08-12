# Web-Style Semantic OsGUI Desktop App in OS-Lang
guiapp LeopardOS:
    title: "Leopard OS Web Desktop"
    width: 1024
    height: 768
    background: "#0f0f1a"

    window DesktopMain:
        header TopBar:
            align: center
            justify: space_between
            bg: "#161625"
            height: 50
            
            label logo:
                text: "Leopard OS"
                color: "#ff0055"
                font_size: 20

            label clock:
                text: "12:00 PM"
                color: "#ffffff"

        container AppBody:
            direction: row
            flex: 1

            sidebar LeftPanel:
                width: 220
                bg: "#1a1a2e"

                button btn_files:
                    text: "📁 Files"
                    bg: "#ff0055"

                button btn_settings:
                    text: "⚙️ Settings"
                    bg: "#22223b"

            main Workspace:
                flex: 1
                bg: "#0f0f1a"
                align: center
                justify: center

                card WelcomeCard:
                    width: 400
                    height: 200
                    bg: "#161625"

                    label msg:
                        text: "Welcome to Bare-Metal Web Desktop!"
                        color: "#00ffcc"

        footer SystemStatus:
            height: 30
            bg: "#10101a"
            align: center

            label status_text:
                text: "System Ready | Memory: 256MB"
                color: "#888888"
