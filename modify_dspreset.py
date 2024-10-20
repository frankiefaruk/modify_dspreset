import xml.etree.ElementTree as ET
import os
from typing import Dict, List, Optional

class DSPresetModifier:
    """
    Decent Sampler .dspreset file modifier for control elements.
    Supports labels, knobs, buttons, and other DS control types.
    """
    
    def __init__(self, file_path: str):
        """Initialize with .dspreset file path."""
        self.file_path = file_path
        self.tree = None
        self.root = None
        self.ui_controls: List[ET.Element] = []
        self.control_types_found: Dict[str, int] = {}
        self._load_file()

    def _load_file(self) -> None:
        """Load and validate the .dspreset file."""
        if not self.file_path.endswith('.dspreset'):
            raise ValueError("File must have .dspreset extension")
        
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        try:
            self.tree = ET.parse(self.file_path)
            self.root = self.tree.getroot()
            
            # Validate basic Decent Sampler structure
            if self.root.tag != 'DecentSampler':
                raise ValueError("Not a valid Decent Sampler preset file (missing DecentSampler root)")
            
            # Find UI controls
            self.ui_controls = self.root.findall('.//control')
            if not self.ui_controls:
                print("Warning: No control elements found in the preset")
            else:
                # Detect available control types
                for control in self.ui_controls:
                    control_type = control.get('type', 'unknown')
                    self.control_types_found[control_type] = self.control_types_found.get(control_type, 0) + 1
                
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML format in {self.file_path}: {e}")

    def create_backup(self) -> str:
        """Create a backup of the original file."""
        backup_path = f"{self.file_path}.backup"
        try:
            with open(self.file_path, 'r', encoding='utf-8') as source:
                with open(backup_path, 'w', encoding='utf-8') as backup:
                    backup.write(source.read())
            print(f"Created backup at: {backup_path}")
            return backup_path
        except IOError as e:
            raise IOError(f"Error creating backup: {e}")

    def modify_controls(self, 
                        selected_types: List[str],
                        x_offset: float = 0, 
                        y_offset: float = 0, 
                        width_offset: float = 0, 
                        height_offset: float = 0,
                        preview: bool = False) -> Dict[str, int]:
        """
        Modify position and size of specified control types.
        Returns dict with modification statistics.
        """
        stats = {'found': 0, 'modified': 0, 'skipped': 0}
        changes = []

        for control in self.ui_controls:
            control_type_attr = control.get('type')
            if control_type_attr in selected_types:
                stats['found'] += 1
                try:
                    # Get current values
                    x = float(control.get('x', 0))
                    y = float(control.get('y', 0))
                    width = float(control.get('width', 0))
                    height = float(control.get('height', 0))
                    
                    # Calculate new values
                    new_x = x + x_offset
                    new_y = y + y_offset
                    new_width = width + width_offset
                    new_height = height + height_offset
                    
                    # Store changes for preview or application
                    change = {
                        'id': control.get('id', control.get('label', 'unnamed')),
                        'type': control_type_attr,
                        'old': {'x': x, 'y': y, 'width': width, 'height': height},
                        'new': {'x': new_x, 'y': new_y, 'width': new_width, 'height': new_height},
                        'element': control
                    }
                    changes.append(change)
                    
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid values for control {control.get('id', 'unnamed')}: {e}")
                    stats['skipped'] += 1
                    continue

        # Apply or preview changes
        if not preview and changes:
            for change in changes:
                control = change['element']
                new_vals = change['new']
                for attr, value in new_vals.items():
                    control.set(attr, str(value))
                stats['modified'] += 1

        # Print changes
        self._print_changes(changes, preview)
        
        return stats

    def _print_changes(self, changes: List[Dict], preview: bool = False) -> None:
        """Print detailed change information."""
        if not changes:
            print("\nNo controls selected for modification.")
            return

        mode = "Preview of changes" if preview else "Applied changes"
        print(f"\n{mode}:")
        print("-" * 50)
        
        for change in changes:
            print(f"Control ID: {change['id']} (Type: {change['type']})")
            for attr in ['x', 'y', 'width', 'height']:
                old_val = change['old'][attr]
                new_val = change['new'][attr]
                if old_val != new_val:
                    print(f"  {attr}: {old_val:>8.1f} → {new_val:>8.1f}")
            print("-" * 30)

    def save(self, output_path: Optional[str] = None) -> None:
        """Save modifications to file."""
        save_path = output_path or self.file_path
        
        try:
            # Create backup before saving
            if not output_path:
                self.create_backup()
            
            self.tree.write(save_path, encoding='utf-8', xml_declaration=True)
            print(f"Successfully saved to: {save_path}")
            
        except IOError as e:
            raise IOError(f"Error saving file: {e}")

def main():
    print("Decent Sampler .dspreset Control Modifier")
    print("----------------------------------------")
    
    # Get file path
    while True:
        file_path = input("Enter path to .dspreset file: ").strip('"')
        if file_path.lower() == 'exit':
            return
        if os.path.exists(file_path) and file_path.endswith('.dspreset'):
            break
        print("Error: Please enter a valid .dspreset file path")
    
    try:
        modifier = DSPresetModifier(file_path)
        
        # Show control types
        print("\nAvailable control types:")
        for control_type, count in modifier.control_types_found.items():
            print(f"- {control_type}: {count} found")
        
        # Select control types to modify
        selected_types = []
        print("\nSelect control types to modify:")
        for control_type in modifier.control_types_found.keys():
            choice = input(f"Modify controls of type '{control_type}'? (y/n): ").strip().lower()
            if choice == 'y':
                selected_types.append(control_type)
        
        if not selected_types:
            print("No control types selected for modification. Exiting.")
            return
        
        # Get offset values
        print("\nEnter offset values (use negative values to decrease):")
        x_offset = float(input("X offset (left/right): "))
        y_offset = float(input("Y offset (up/down): "))
        width_offset = float(input("Width change: "))
        height_offset = float(input("Height change: "))
        
        # Preview changes
        stats = modifier.modify_controls(
            selected_types=selected_types,
            x_offset=x_offset,
            y_offset=y_offset,
            width_offset=width_offset,
            height_offset=height_offset,
            preview=True
        )
        
        if stats['found'] == 0:
            print("\nNo controls found for the selected types.")
            return
        
        # Confirm changes
        if input("\nApply these changes? (y/n): ").lower() == 'y':
            stats = modifier.modify_controls(
                selected_types=selected_types,
                x_offset=x_offset,
                y_offset=y_offset,
                width_offset=width_offset,
                height_offset=height_offset
            )
            modifier.save()
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
