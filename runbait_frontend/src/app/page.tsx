import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";

import HowItWorks from "@/components/HowItWorks";
import Features from "@/components/Features";
import CTA from "@/components/CTA";
import Footer from "@/components/Footer";
import FadeIn from "@/components/FadeIn";

export default function Home() {
  return (
    <div className="min-h-screen selection:bg-white/20">
      <Navbar />
      <main>
        <FadeIn delay={100}><Hero /></FadeIn>

        <FadeIn delay={200}><HowItWorks /></FadeIn>
        <FadeIn delay={200}><Features /></FadeIn>
        <FadeIn delay={200}><CTA /></FadeIn>
      </main>
      <Footer />
    </div>
  );
}
