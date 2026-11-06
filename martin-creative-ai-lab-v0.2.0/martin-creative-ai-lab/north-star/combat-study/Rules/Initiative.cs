using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace NorthStar.Combat
{
    // Original bounded two-actor policy; source requirements do not prescribe these numbers.
    public sealed class InitiativeOrder
    {
        public int Round { get; }
        public int PlayerScore { get; }
        public int TargetScore { get; }
        public uint SeedState { get; }
        public IReadOnlyList<string> Order { get; }
        internal InitiativeOrder(int round,int player,int target,uint state,bool playerFirst)
        {
            Round=round;PlayerScore=player;TargetScore=target;SeedState=state;
            Order=new ReadOnlyCollection<string>(playerFirst?new[]{"player","target"}:new[]{"target","player"});
        }
    }
    public sealed class Initiative
    {
        public const uint DefaultSeed=0x4e535441;
        private uint state;
        public string Style { get; }
        public int PlayerAgility => Style=="heavy"?8:16;
        public int TargetAgility => 12;
        public int StrikeDamage => Style=="heavy"?32:16;
        public int BashDamage => Style=="heavy"?18:10;
        public InitiativeOrder Current { get; private set; }
        public Initiative(string style,uint seed=DefaultSeed)
        {
            if(style!="heavy"&&style!="quick")throw new ArgumentException("Exact heavy or quick tempo required.");
            Style=style;state=seed;Current=Generate(1);
        }
        private uint Next(){unchecked{state=state*1664525u+1013904223u;}return state;}
        private InitiativeOrder Generate(int round)
        {
            int player=PlayerAgility+(int)(Next()%13)-6;
            int target=TargetAgility+(int)(Next()%13)-6;
            bool first=player>target||(player==target&&(Next()&1)==0);
            return new InitiativeOrder(round,player,target,state,first);
        }
        // Exactly one call after a surviving global round; reads cannot advance the PRNG.
        public void Advance(){Current=Generate(checked(Current.Round+1));}
    }
}
