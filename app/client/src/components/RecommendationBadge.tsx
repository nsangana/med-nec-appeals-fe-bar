import { Badge } from '@databricks/appkit-ui/react';
import { CheckCircle2, MinusCircle, TriangleAlert } from 'lucide-react';

// WARRANTED = actionable / positive → success token.
// NEEDS REVIEW = a human must decide before any letter goes out → warning token.
// NOT WARRANTED = no appeal action → muted secondary.
export function RecommendationBadge({ recommendation }: { recommendation: string }) {
  if (recommendation === 'WARRANTED') {
    return (
      <Badge
        className="gap-1 border-transparent"
        style={{
          backgroundColor: 'var(--success)',
          color: 'var(--success-foreground)',
        }}
      >
        <CheckCircle2 className="h-3.5 w-3.5" />
        WARRANTED
      </Badge>
    );
  }

  if (recommendation === 'NEEDS REVIEW') {
    return (
      <Badge
        className="gap-1 border-transparent"
        style={{
          backgroundColor: 'var(--warning)',
          color: 'var(--warning-foreground)',
        }}
      >
        <TriangleAlert className="h-3.5 w-3.5" />
        NEEDS REVIEW
      </Badge>
    );
  }

  if (recommendation === 'NOT GENERATED') {
    return <Badge variant="outline" className="text-muted-foreground">Not generated</Badge>;
  }

  return (
    <Badge variant="secondary" className="gap-1 text-muted-foreground">
      <MinusCircle className="h-3.5 w-3.5" />
      NOT WARRANTED
    </Badge>
  );
}
