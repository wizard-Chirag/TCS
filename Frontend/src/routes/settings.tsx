import { createFileRoute } from "@tanstack/react-router";
import { User, Palette, Bot, Globe, Bell, Lock } from "lucide-react";
import { toast } from "sonner";
import { Container, PageHeader } from "@/components/page-header";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { actions } from "@/lib/store";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — MedBrief AI" },
      { name: "description", content: "Profile, AI preferences, language, notifications and privacy settings." },
      { property: "og:title", content: "Settings — MedBrief AI" },
      { property: "og:description", content: "Manage your MedBrief AI workspace settings." },
    ],
  }),
  component: Settings,
});

function Block({ icon: Icon, title, children }: { icon: typeof User; title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border bg-card p-5 shadow-soft sm:p-6">
      <h2 className="mb-4 flex items-center gap-2 font-semibold"><Icon className="size-4 text-primary" /> {title}</h2>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

function Toggle({ label, desc, on }: { label: string; desc: string; on?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div><div className="text-sm font-medium">{label}</div><div className="text-xs text-muted-foreground">{desc}</div></div>
      <Switch defaultChecked={!!on} />
    </div>
  );
}

function Settings() {
  return (
    <Container>
      <PageHeader title="Settings" subtitle="Personalize your research workspace." actions={<Button variant="hero" onClick={() => toast.success("Settings saved")}>Save changes</Button>} />
      <div className="grid gap-5 lg:grid-cols-2">
        <Block icon={User} title="Profile">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5"><Label>Name</Label><Input defaultValue="Dr. Alex Morgan" /></div>
            <div className="space-y-1.5"><Label>Role</Label><Input defaultValue="Clinical researcher" /></div>
          </div>
          <div className="space-y-1.5"><Label>Email</Label><Input defaultValue="alex@example.com" /></div>
        </Block>
        <Block icon={Bot} title="AI preferences">
          <Label>Default summary length</Label>
          <RadioGroup defaultValue="standard" className="grid grid-cols-3 gap-2">
            {["brief", "standard", "detailed"].map((v) => (
              <Label key={v} className="flex cursor-pointer items-center gap-2 rounded-xl border p-3 capitalize has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-accent">
                <RadioGroupItem value={v} /> {v}
              </Label>
            ))}
          </RadioGroup>
          <Toggle label="Include numerical results" desc="Prioritize effect sizes and confidence intervals" on />
          <Toggle label="Plain-language mode" desc="Explain terms for students" />
        </Block>
        <Block icon={Palette} title="Appearance">
          <Toggle label="Compact layout" desc="Denser cards and lists" />
          <Toggle label="Reduce motion" desc="Minimize animations" />
        </Block>
        <Block icon={Globe} title="Language">
          <Select defaultValue="en">
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="en">English</SelectItem>
              <SelectItem value="es">Español</SelectItem>
              <SelectItem value="fr">Français</SelectItem>
              <SelectItem value="de">Deutsch</SelectItem>
              <SelectItem value="hi">हिन्दी</SelectItem>
            </SelectContent>
          </Select>
        </Block>
        <Block icon={Bell} title="Notifications">
          <Toggle label="Summary ready" desc="Notify when processing completes" on />
          <Toggle label="Weekly digest" desc="Recap of your research activity" />
        </Block>
        <Block icon={Lock} title="Data & privacy">
          <Toggle label="Store uploaded documents" desc="Keep originals for re-analysis" on />
          <Button variant="outline" className="rounded-full" onClick={() => { actions.reset(); toast.success("Demo data restored"); }}>Reset demo data</Button>
        </Block>
      </div>
    </Container>
  );
}
