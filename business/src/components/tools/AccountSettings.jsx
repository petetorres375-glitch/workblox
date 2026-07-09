import ToolPicker from "./ToolPicker";

export default function AccountSettings({ onSaved }) {
  return <ToolPicker variant="settings" onDone={onSaved} />;
}
