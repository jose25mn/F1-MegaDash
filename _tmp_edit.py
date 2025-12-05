from pathlib import Path
path = Path('client/src/pages/OverviewPage.tsx')
lines = path.read_text(encoding='utf-8').splitlines()
start = None
end = None
for i, l in enumerate(lines):
    if l.strip().startswith('<DashboardCard'):
        start = i
        break
for i in range(start + 1 if start is not None else 0, len(lines)):
    if '</DashboardCard' in lines[i]:
        end = i
        break
if start is None or end is None:
    raise SystemExit('markers not found')
block = '''        <DashboardCard
          title="Pista da temporada - top equipes"
          subtitle="Cada prova como bloco: vitoria, podio, top 10 ou fora do top 10"
        >
          {constructorLanes && (constructorLanes as any).lanes?.length ? (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-3 items-center text-xs text-white/70">
                <div className="flex items-center gap-1">
                  <span className="inline-block h-3 w-5 rounded bg-amber-400"></span> Vitoria
                </div>
                <div className="flex items-center gap-1">
                  <span className="inline-block h-3 w-5 rounded bg-amber-200/80"></span> Podio
                </div>
                <div className="flex items-center gap-1">
                  <span className="inline-block h-3 w-5 rounded bg-emerald-400/60"></span> Top 10
                </div>
                <div className="flex items-center gap-1">
                  <span className="inline-block h-3 w-5 rounded bg-white/10"></span> Fora do Top 10 / DNF
                </div>
              </div>

              <div className="space-y-2 overflow-x-auto pb-1">
                {(constructorLanes as any).lanes.map((lane: any, laneIdx: number) => (
                  <div key={lane.constructorId} className="space-y-1 min-w-[520px]">
                    <div className="flex items-center gap-2">
                      <div className="w-32 text-sm font-semibold text-white/90 truncate">
                        {lane.constructor_name}
                      </div>
                      <div className="flex-1 flex gap-1">
                        {lane.slots.map((slot: any, idx: number) => {
                          const status = slot.status as string;
                          const colors: Record<string, string> = {
                            win: "bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]",
                            podium: "bg-amber-200/80",
                            top10: "bg-emerald-400/60",
                            other: "bg-white/10",
                            dns: "bg-white/5",
                          };
                          const title =
                            slot.grand_prix && slot.pos
                              ? `${slot.grand_prix} - P${slot.pos}`
                              : slot.grand_prix
                                ? slot.grand_prix
                                : `Prova ${slot.round}`;
                          return (
                            <div
                              key={`${laneIdx}-${idx}`}
                              className={`h-5 w-5 rounded-sm ${colors[status] ?? "bg-white/10"}`}
                              title={title}
                            ></div>
                          );
                        })}
                      </div>
                      <div className="w-12 text-right text-xs text-white/60">
                        P{lane.slots[lane.slots.length - 1]?.pos ?? "--"}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex gap-1 text-[10px] text-white/50 overflow-x-auto">
                <div className="w-32"></div>
                <div className="flex gap-1 min-w-[520px]">
                  {(constructorLanes as any).rounds.map((round: number) => (
                    <div key={round} className="w-5 text-center">
                      {round}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-sm text-white/60">Carregando pista...</div>
          )}
        </DashboardCard'''.splitlines()
lines = lines[:start] + block + lines[end+1:]
path.write_text("\n".join(lines) + "\n", encoding='utf-8')
