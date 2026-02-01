import { CalendarIcon, FileTextIcon } from "@radix-ui/react-icons"
import { Globe, Share2Icon } from "lucide-react"

import { cn } from "@/lib/utils"
import { Calendar } from "@/components/ui/calendar"
import { BentoCard, BentoGrid } from "@/components/ui/bento-grid"
import { Marquee } from "@/components/ui/marquee"
import { AnimatedBeamMultipleOutput } from "@/components/custom/animated-beam-multiple-outputs"
import { WorldMap } from "@/components/custom/world-map"

const files = [
  {
    name: "E3 - Ethics.pdf",
    body: "Pharmaceutical ethics ensures patient safety by guiding responsible research practices, transparent reporting, informed consent, and regulatory compliance across drug development.",
  },
  {
    name: "E10 - Medicine.pdf",
    body: "Modern medicine relies on pharmaceutical innovation to develop safe, effective therapies that improve outcomes, manage diseases, and enhance patient quality of life.",
  },
  {
    name: "E5 - Structure.pdf",
    body: "Drug structure analysis examines molecular composition to optimize stability, bioavailability, and therapeutic activity while minimizing adverse effects during formulation.",
  },
  {
    name: "E7 - Review.pdf",
    body: "Pharmaceutical reviews critically evaluate clinical data, safety profiles, and efficacy results to support regulatory decisions and evidence-based treatment guidelines.",
  },
  {
    name: "E23 - Trials.pdf",
    body: "Clinical trials systematically assess investigational drugs in controlled settings to determine safety, dosage, and effectiveness before regulatory approval.",
  },
];

const features = [
  {
    Icon: FileTextIcon,
    name: "Knowledge Ingestion",
    description: "Where files become intelligent context.",
    href: "#",
    cta: "Learn more",
    className: "col-span-3 lg:col-span-1",
    background: (
      <Marquee
        pauseOnHover
        className="absolute top-10 [mask-image:linear-gradient(to_top,transparent_40%,#000_100%)] [--duration:20s]"
      >
        {files.map((f, idx) => (
          <figure
            key={idx}
            className={cn(
              "relative w-32 cursor-pointer overflow-hidden rounded-xl border p-4",
              "border-gray-950/[.1] bg-gray-950/[.01] hover:bg-gray-950/[.05]",
              "dark:border-gray-50/[.1] dark:bg-gray-50/[.10] dark:hover:bg-gray-50/[.15]",
              "transform-gpu blur-[1px] transition-all duration-300 ease-out hover:blur-none"
            )}
          >
            <div className="flex flex-row items-center gap-2">
              <div className="flex flex-col">
                <figcaption className="text-sm font-medium dark:text-white">
                  {f.name}
                </figcaption>
              </div>
            </div>
            <blockquote className="mt-2 text-xs">{f.body}</blockquote>
          </figure>
        ))}
      </Marquee>
    ),
  },
  {
    Icon: Globe,
    name: "Engineering the Standard",
    description: "Ready to build what scales, standardize what matters, and lead forward.",
    href: "#",
    cta: "Learn more",
    className: "col-span-3 lg:col-span-2",
    background: (
      <WorldMap/>
    ),
  },
  {
    Icon: Share2Icon,
    name: "Integrations",
    description: "Connect tools. Expand intelligence. Automate workflows.",
    href: "#",
    cta: "Learn more",
    className: "col-span-3 lg:col-span-2",
    background: (
      <AnimatedBeamMultipleOutput className="absolute top-4 right-2 h-[300px] border-none [mask-image:linear-gradient(to_top,transparent_10%,#000_100%)] transition-all duration-300 ease-out group-hover:scale-105" />
    ),
  },
  {
    Icon: CalendarIcon,
    name: "Calendar",
    description: "Use the calendar to arrange our next interview.",
    className: "col-span-3 lg:col-span-1",
    href: "#",
    cta: "Schedule it now",
    background: (
      <Calendar
        mode="single"
        selected={new Date(2022, 4, 11, 0, 0, 0)}
        className="absolute top-10 right-0 origin-top scale-75 rounded-md border [mask-image:linear-gradient(to_top,transparent_40%,#000_100%)] transition-all duration-300 ease-out group-hover:scale-90"
      />
    ),
  },
]

export default function HopePage() {
  return (
    <div  className="flex-1 flex pt-4">
      <BentoGrid>
        {features.map((feature, idx) => (
          <BentoCard key={idx} {...feature} />
        ))}
      </BentoGrid>
    </div>
  )
}
