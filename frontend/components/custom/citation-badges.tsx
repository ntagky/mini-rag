import { Badge } from "@/components/ui/badge";
import { ArrowUpRightIcon } from "lucide-react";

export default function CitationBadges({ citations }: { citations: string[] }) {
  if (!citations || citations.length === 0) return null;

  const firstTwo = citations.slice(0, 2);
  const extraCount = citations.length - 2;

  return (
    <div className="flex gap-1">
      {firstTwo.map((file, idx) => (
        <Badge asChild key={idx}>
          <a href={`#${file}`}>
            {file} <ArrowUpRightIcon data-icon="inline-end" />
          </a>
        </Badge>
      ))}

      {extraCount > 0 && (
        <Badge asChild>
          <a href={``}>
            +{extraCount}
          </a>
        </Badge>
      )}
    </div>
  );
}
