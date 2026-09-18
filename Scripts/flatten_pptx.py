import os
import shutil
import tempfile
import time
from pptx import Presentation
try:
    import win32com.client
    import pythoncom
except ImportError:
    win32com = None
    pythoncom = None

def flatten_presentation(pptx_path):
    """
    Converts a PPTX file where all content is replaced by high-resolution images of the original slides.
    Ensures the information is non-editable while preserving visual appearance.
    
    Args:
        pptx_path: Path to the .pptx file to flatten.
    
    Returns:
        True if flattening succeeded, False otherwise.
    
    Raises:
        RuntimeError: If flattening fails, so callers can handle the error visibly.
    """
    if win32com is None or pythoncom is None:
        raise RuntimeError("pywin32 is not installed. Cannot flatten slides. Install with: pip install pywin32")

    print(f" [FLATTEN] Starting flattening process for: {os.path.basename(pptx_path)}")
    
    if not os.path.exists(pptx_path):
        raise RuntimeError(f"File not found: {pptx_path}")

    # Get absolute path for win32com
    abs_pptx_path = os.path.abspath(pptx_path)
    
    # Create temp directory for images
    temp_dir = tempfile.mkdtemp()
    
    # Track COM objects for cleanup
    powerpoint = None
    presentation = None
    com_initialized = False
    
    try:
        # ============================================================
        # FIX: Initialize COM for the current thread.
        # Streamlit runs callbacks in secondary threads, and COM 
        # requires CoInitialize() to be called on each thread before
        # any COM objects can be used.
        # ============================================================
        pythoncom.CoInitialize()
        com_initialized = True
        
        # 1. Export original slides to images using PowerPoint application via COM
        powerpoint = win32com.client.Dispatch("PowerPoint.Application")
        
        presentation = powerpoint.Presentations.Open(abs_pptx_path, WithWindow=False)
        
        # Export each slide as PNG at high resolution
        presentation.Export(temp_dir, "PNG", ScaleWidth=1920, ScaleHeight=1080)
        presentation.Close()
        presentation = None
        
        # Always quit PowerPoint to avoid orphaned processes
        powerpoint.Quit()
        powerpoint = None
        
        # 2. Rebuild the presentation with images using python-pptx for speed and clean XML
        # Open original to get slide dimensions
        orig_prs = Presentation(pptx_path)
        new_prs = Presentation()
        new_prs.slide_width = orig_prs.slide_width
        new_prs.slide_height = orig_prs.slide_height
        
        # Slides are exported to temp_dir/Slide1.PNG, Slide2.PNG, etc.
        # Sometimes presentation.Export creates a subfolder within temp_dir
        filenames = os.listdir(temp_dir)
        
        # Check if they are in a subfolder
        export_folder = temp_dir
        if len(filenames) == 1 and os.path.isdir(os.path.join(temp_dir, filenames[0])):
            export_folder = os.path.join(temp_dir, filenames[0])
            filenames = os.listdir(export_folder)
            
        # Filter and sort PNGs
        png_files = [f for f in filenames if f.lower().endswith('.png')]
        
        # Sort by slide number (Slide1.png, Slide2.png... Slide10.png)
        def get_slide_num(name):
            try:
                num_str = name.lower().replace('slide', '').replace('.png', '')
                return int(num_str)
            except:
                return 0
        
        png_files.sort(key=get_slide_num)
        
        if not png_files:
            raise RuntimeError("No images were exported from the presentation. PowerPoint export may have failed.")

        print(f" [FLATTEN] Rebuilding deck with {len(png_files)} images...")
        
        # Use a blank layout for new slides
        blank_layout = new_prs.slide_layouts[6]
        
        for png in png_files:
            slide = new_prs.slides.add_slide(blank_layout)
            img_path = os.path.join(export_folder, png)
            slide.shapes.add_picture(img_path, 0, 0, new_prs.slide_width, new_prs.slide_height)
            
        # Wait briefly for file handles to clear, then save over the original
        time.sleep(0.5)
        new_prs.save(pptx_path)
        print(f" [FLATTEN] Success! Presentation flattened: {os.path.basename(pptx_path)}")
        return True
        
    except Exception as e:
        print(f" [!] ERROR during flattening: {e}")
        import traceback
        traceback.print_exc()
        # Re-raise as RuntimeError so the caller can show it in the UI
        raise RuntimeError(f"Flatten failed for {os.path.basename(pptx_path)}: {e}") from e
    finally:
        # Cleanup COM objects
        try:
            if presentation is not None:
                presentation.Close()
        except:
            pass
        try:
            if powerpoint is not None:
                powerpoint.Quit()
        except:
            pass
        # Uninitialize COM for this thread
        if com_initialized:
            try:
                pythoncom.CoUninitialize()
            except:
                pass
        # Cleanup temp files
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
