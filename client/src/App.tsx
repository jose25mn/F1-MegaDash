import { useState } from "react";
import { Switch, Route } from "wouter";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

// Pages
import { OverviewPage } from "@/pages/OverviewPage";
import { SeasonPage } from "@/pages/SeasonPage";
import { CircuitsPage } from "@/pages/CircuitsPage";
import { TeamsPage } from "@/pages/TeamsPage";
import { DriversPage } from "@/pages/DriversPage";
import NotFound from "@/pages/not-found";

function App() {
  const [view, setView] = useState<"overview" | "season" | "circuits" | "teams" | "drivers">("overview");
  const [season, setSeason] = useState(2024);

  const seasons = Array.from({ length: 2024 - 1950 + 1 }, (_, i) => 2024 - i);

  const renderPage = () => {
    switch (view) {
      case "overview": return <OverviewPage season={season} />;
      case "season": return <SeasonPage season={season} />;
      case "circuits": return <CircuitsPage season={season} />;
      case "teams": return <TeamsPage season={season} />;
      case "drivers": return <DriversPage season={season} />;
      default: return <OverviewPage season={season} />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/20">
          
          {/* Barra de navegação superior */}
          <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
              
              {/* Logo / Título */}
              <div className="flex items-center gap-2 mr-8">
                <div className="w-8 h-8 bg-primary skew-x-[-10deg] flex items-center justify-center shadow-[0_0_15px_rgba(225,6,0,0.5)]">
                  <span className="font-display font-bold text-white text-lg skew-x-[10deg]">F1</span>
                </div>
                <span className="hidden md:block font-display font-bold text-xl tracking-wider text-white uppercase">
                  Mega<span className="text-primary">Dash</span>
                </span>
              </div>

              {/* Abas de navegação */}
              <nav className="hidden md:flex items-center gap-1">
                {[
                  { key: "overview", label: "Visão Geral" },
                  { key: "season", label: "Temporada" },
                  { key: "circuits", label: "Circuitos" },
                  { key: "teams", label: "Equipes" },
                  { key: "drivers", label: "Pilotos" },
                ].map((tab) => {
                  const isActive = view === tab.key;
                  return (
                    <button
                      key={tab.key}
                      onClick={() => setView(tab.key as any)}
                      className={cn(
                        "px-4 py-2 text-sm font-bold uppercase tracking-wider transition-all rounded-sm clip-path-slant",
                        isActive 
                          ? "text-white bg-white/10 border-b-2 border-primary shadow-[0_0_10px_rgba(255,255,255,0.05)]" 
                          : "text-white/60 hover:text-white hover:bg-white/5"
                      )}
                    >
                      {tab.label}
                    </button>
                  );
                })}
              </nav>

              {/* Navegação mobile (simplificada) */}
              <div className="md:hidden flex-1 px-4">
                 <Select value={view} onValueChange={(v: any) => setView(v)}>
                    <SelectTrigger className="w-full bg-white/5 border-white/10 text-white">
                      <SelectValue placeholder="Escolha a seção" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="overview">Visão Geral</SelectItem>
                      <SelectItem value="season">Temporada</SelectItem>
                      <SelectItem value="circuits">Circuitos</SelectItem>
                      <SelectItem value="teams">Equipes</SelectItem>
                      <SelectItem value="drivers">Pilotos</SelectItem>
                    </SelectContent>
                 </Select>
              </div>

              {/* Seletor de temporada */}
              <div className="flex items-center gap-3 pl-4 border-l border-white/10">
                <span className="hidden lg:inline text-xs text-white/40 font-bold uppercase tracking-widest">Temporada</span>
                <Select value={season.toString()} onValueChange={(v) => setSeason(parseInt(v))}>
                  <SelectTrigger className="w-[100px] bg-primary text-white border-none font-bold font-mono shadow-[0_0_10px_rgba(225,6,0,0.3)] focus:ring-primary/50">
                    <SelectValue placeholder="Ano" />
                  </SelectTrigger>
                  <SelectContent className="max-h-[300px]">
                    {seasons.map((y) => (
                      <SelectItem key={y} value={y.toString()} className="font-mono">{y}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

            </div>
          </header>

          {/* Main Content Area */}
          <main className="container mx-auto px-4 py-8 min-h-[calc(100vh-64px)]">
            <div className="max-w-7xl mx-auto">
              {renderPage()}
            </div>
          </main>

        </div>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
