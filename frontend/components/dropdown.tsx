import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";

type DropdownProps = {
  items: { value: string; label: string }[];
  value: string;
  onChange?: (value: string | null) => void;
  label?: string;
  name?: string;
};
export function Dropdown({
  items,
  value,
  onChange,
  label,
  name,
}: DropdownProps) {
  return (
    <Select name={name} value={value} onValueChange={onChange} items={items}>
      <div className="flex flex-col gap-1">
        {label && <div className="font-medium text-sm">{label}</div>}
        <SelectTrigger className="w-56 bg-white" aria-label="Lig">
          <SelectValue />
        </SelectTrigger>
      </div>

      <SelectContent>
        {items.map((item) => (
          <SelectItem key={item.value} value={item.value}>
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
