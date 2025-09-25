        rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        darker_rgb = tuple(int(c * factor) for c in rgb)
        return f"rgb({darker_rgb[0]}, {darker_rgb[1]}, {darker_rgb[2]})"


class HighlightCard(QFrame):
    def __init__(self, highlight, index):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(
            """
            QFrame {
                background-color: white;
                border: 1px solid #E0E6ED;
                border-radius: 10px;
                padding: 8px 12px;
                margin: 4px;
                min-height: 60px;
                max-height: 110px;
            }
            QFrame:hover {
                border-color: #6C5CE7;
                box-shadow: 0 2px 6px rgba(108, 92, 231, 0.10);
            }
        """
        )
