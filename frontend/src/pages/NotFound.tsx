import { Link } from "react-router-dom";
import { Compass } from "lucide-react";
import { EmptyState, useTitle } from "../ui";

export default function NotFound() {
  useTitle("Page not found");
  return (
    <div style={{ paddingTop: 60 }}>
      <EmptyState icon={Compass} title="This page doesn't exist" actions={<><Link className="btn primary" to="/">Go to overview</Link><Link className="btn" to="/catalog">Browse tables</Link></>}>
        The link may be out of date, or the table may have been removed from the lake.
      </EmptyState>
    </div>
  );
}
