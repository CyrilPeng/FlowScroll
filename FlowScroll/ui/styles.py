from FlowScroll.platform import OS_NAME

def get_main_stylesheet():
    font_family = (
        "'.AppleSystemUIFont', 'SF Pro Text', sans-serif"
        if OS_NAME == "Darwin"
        else "'Segoe UI', 'Microsoft YaHei', sans-serif"
    )
    return f"""
        QMainWindow {{ background-color: #0F172A; font-family: {font_family}; }}
        QScrollArea {{ border: none; background-color: transparent; }}
        QScrollArea > QWidget > QWidget {{ background-color: transparent; }}
        
        /* Custom Scrollbar for modern look */
        QScrollBar:vertical {{ border: none; background: #0F172A; width: 6px; margin: 0px; }}
        QScrollBar::handle:vertical {{ background: #334155; border-radius: 3px; min-height: 20px; }}
        QScrollBar::handle:vertical:hover {{ background: #475569; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        
        QLabel {{ color: #F8FAFC; font-size: 14px; }}
        QLabel#HeaderTitle {{ font-size: 28px; font-weight: 800; color: #F8FAFC; letter-spacing: 0.5px; }}
        QLabel#HeaderSubtitle {{ font-size: 13px; color: #64748B; font-weight: 600; margin-top: -4px; }}
        QLabel#SectionTitle {{ font-size: 12px; font-weight: 700; color: #94A3B8; margin-top: 12px; margin-bottom: 4px; padding-left: 4px; padding-right: 12px; }}
        
        QFrame#Card {{ background-color: #1E293B; border-radius: 16px; border: 1px solid #334155; }}
        QFrame#Separator {{ background-color: #334155; max-height: 1px; }}
        
        QDoubleSpinBox {{ background-color: #0F172A; border: 1px solid #334155; border-radius: 8px; padding: 4px; color: #3B82F6; font-weight: 700; font-size: 14px; }}
        QDoubleSpinBox:focus {{ border: 1px solid #3B82F6; background-color: #0B1120; }}
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0px; height: 0px; }}
        
        QSlider::groove:horizontal {{ border-radius: 4px; height: 8px; background: #334155; }}
        QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6); border-radius: 4px; }}
        QSlider::handle:horizontal {{ background: #FFFFFF; border: 2px solid #3B82F6; width: 18px; height: 18px; margin: -5px 0; border-radius: 9px; }}
        QSlider::handle:horizontal:hover {{ background: #EFF6FF; border: 3px solid #2563EB; }}

        QCheckBox {{ color: #E2E8F0; font-size: 14px; font-weight: 600; spacing: 12px; min-height: 24px; }}
        QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 6px; border: 2px solid #475569; background-color: #0F172A; }}
        QCheckBox::indicator:hover {{ border-color: #64748B; }}
        QCheckBox::indicator:checked {{ background-color: #3B82F6; border-color: #3B82F6; }}
        
        QTabWidget::pane {{ border: none; background-color: transparent; }}
        QTabBar::tab {{ background: #0F172A; color: #94A3B8; font-weight: 700; font-size: 14px; padding: 12px 24px; border: none; border-bottom: 2px solid transparent; }}
        QTabBar::tab:hover {{ color: #E2E8F0; }}
        QTabBar::tab:selected {{ color: #3B82F6; border-bottom: 2px solid #3B82F6; }}
        
        QPushButton {{ background-color: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 8px 16px; color: #F8FAFC; font-weight: 600; font-size: 13px; }}
        QPushButton:hover {{ background-color: #334155; border-color: #475569; }}
        QPushButton:pressed {{ background-color: #0F172A; }}
        
        QPushButton#BtnPrimary {{ background-color: #3B82F6; color: #FFFFFF; border: none; padding: 10px 16px; font-size: 14px; border-radius: 10px; }}
        QPushButton#BtnPrimary:hover {{ background-color: #2563EB; }}
        QPushButton#BtnPrimary:pressed {{ background-color: #1D4ED8; }}
        
        QPushButton#BtnDanger {{ background-color: #450A0A; color: #FCA5A5; border: 1px solid #7F1D1D; border-radius: 10px; }}
        QPushButton#BtnDanger:hover {{ background-color: #7F1D1D; color: #FECACA; }}
        QPushButton#BtnDanger:pressed {{ background-color: #450A0A; }}
        
        QPushButton#BtnAdv {{ background-color: #1E293B; border: 1px solid #3B82F6; color: #60A5FA; border-radius: 10px; padding: 12px; font-weight: 700; font-size: 14px; text-align: center; }}
        QPushButton#BtnAdv:hover {{ background-color: #172554; border-color: #60A5FA; }}
        
        QPushButton#BtnIcon {{ background: transparent; border: none; padding: 6px; border-radius: 8px; }}
        QPushButton#BtnIcon:hover {{ background-color: #1E293B; }}
        
        QComboBox {{ background-color: #0F172A; border: 1px solid #334155; border-radius: 10px; padding: 8px 12px; color: #F8FAFC; font-weight: 600; font-size: 13px; }}
        QComboBox::drop-down {{ border: none; width: 30px; }}
        QComboBox::down-arrow {{ image: none; }}
        
        QKeySequenceEdit {{ border: 1px solid #334155; border-radius: 8px; padding: 4px 12px; background: #0F172A; color: #3B82F6; font-weight: 700; font-size: 14px; min-width: 60px; }}
        QKeySequenceEdit:focus {{ border: 1px solid #3B82F6; background: #0B1120; }}
    """
