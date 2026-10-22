using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using NorthStar.Narrative;
using P=NorthStar.Narrative.Program;

namespace NorthStar.NarrativeChecks
{
    public static class Program
    {
        private static readonly List<string> Controls=new List<string>();
        private static string State(RequestExpedition g)=>JsonSerializer.Serialize(g.Snapshot());
        private static void Check(string id,bool condition){if(!condition)throw new InvalidOperationException("FAIL: "+id);if(Controls.Contains(id))throw new InvalidOperationException("Duplicate control.");Controls.Add(id);}
        private static void Reject(string id,RequestExpedition g,string command){string before=State(g);Check(id+"_refused",!g.Command(command));Check(id+"_whole_state_unchanged",State(g)==before);}
        private static void Run(RequestExpedition g,IEnumerable<string> commands){foreach(string command in commands)if(!g.Command(command))throw new InvalidOperationException("Fixture refused "+command+": "+g.Last);}
        private static RequestExpedition Surveyed(){var g=new RequestExpedition();Run(g,P.SurveyPath);return g;}
        private static RequestExpedition Committed(string term="dusk"){var g=Surveyed();Run(g,new[]{"open","hear","offer","terms "+term,"confirm"});return g;}
        public static int Main(string[] args)
        {
            try
            {
                var g=new RequestExpedition();Check("initial_no_delivery",!g.Delivered&&!g.Returned&&g.Crates==0&&g.Remaining==4&&g.GuideAvailable);
                Reject("no_fabricated_finish",g,"complete");Reject("unknown_shape",g,"work extra");Reject("unknown_term",g,"terms instant");Reject("no_unsurveyed_departure",g,"depart solo");Reject("no_unsolicited_consent",g,"hear");
                Check("open_request",g.Open());Reject("unsurveyed_refusal",g,"hear");Reject("offer_without_consent",g,"offer");Check("unsurveyed_refusal_stages_action",g.Last.Length>0);
                Check("decline_supported",g.Decline());Check("decline_keeps_guide",g.GuideAvailable&&g.Status=="declined"&&!g.Delivered);Reject("final_refusal_not_deferral",g,"open");
                Run(g,new[]{"work","work","work"});Check("local_refusal_finishes_shutters",g.Crates==5&&g.Shift==3&&!g.Delivered);Reject("finished_work_noextra_time",g,"work");
                g=new RequestExpedition();Check("defer_supported",g.Defer());Check("defer_is_no_promise",g.Status=="deferred"&&g.GuideAvailable&&g.Term==null);Reject("defer_no_confirm",g,"confirm");
                g=Surveyed();Check("actual_survey_complete",g.Surveyed&&g.Shift==1&&!g.Active&&!g.Delivered);Reject("survey_cannot_repeat",g,"survey");
                Run(g,new[]{"open","hear","offer"});Check("tentative_keeps_guide",g.GuideAvailable&&g.Term==null&&g.Conversation=="terms");Reject("missing_terms",g,"confirm");Reject("invalid_terms",g,"terms forever");
                Run(g,new[]{"terms dusk"});Check("terms_not_departure",g.GuideAvailable&&g.Term==null&&!g.Returned);Check("work_during_draft",g.Work());Check("work_invalidates_conversation",g.Conversation=="closed");Reject("stale_terms",g,"confirm");Run(g,new[]{"open"});Reject("stale_consent",g,"offer");Run(g,new[]{"hear","offer","terms open","confirm"});Check("fresh_consent_commits",g.Status=="committed"&&!g.GuideAvailable&&g.Term=="open"&&!g.Delivered&&!g.Returned);
                Reject("duplicate_commit",g,"confirm");Reject("commit_not_retroactive_decline",g,"decline");Reject("commit_not_defer",g,"defer");Reject("guided_ownership_blocks_solo",g,"depart solo");
                Check("withdraw_before_departure",g.Withdraw());Check("withdraw_restores_availability",g.GuideAvailable&&g.Status=="deferred"&&g.Term==null);Check("withdraw_keeps_original_receipt",JsonDocument.Parse(State(g)).RootElement.GetProperty("receipts").GetArrayLength()==2);
                g=Committed();Check("commitment_no_result",!g.Delivered&&!g.Returned);Check("guided_departure",g.Depart("guided"));Check("guided_cost_two_shifts",g.Shift==3&&g.Remaining==1&&!g.GuideAvailable&&g.Active&&!g.Delivered);
                Reject("no_work_while_away_playing",g,"work");Reject("no_conversation_during_crossing",g,"open");Reject("departure_not_repeatable",g,"depart guided");Reject("cannot_refund_departed_guide",g,"withdraw");
                Run(g,P.DeliveryPath);Check("actual_handoff_proves_result",g.Delivered&&g.Returned&&g.GuideAvailable&&g.Status=="delivered");Check("actual_model_reward_once",JsonDocument.Parse(State(g)).RootElement.GetProperty("encounter").GetProperty("xp").GetInt32()==25);Reject("finished_crossing_no_reward_farm",g,"skill");Reject("delivered_no_new_offer",g,"open");Run(g,new[]{"work"});Check("guided_tradeoff_retained",g.Crates==2&&g.Remaining==0);Reject("daylight_exhausted",g,"work");
                g=Surveyed();Run(g,new[]{"decline","depart solo"});Check("solo_no_guide_consent_gate",g.GuideAvailable&&g.Active&&g.Shift==4&&g.Term=="solo");Run(g,P.DeliveryPath);Check("solo_actual_handoff",g.Delivered&&g.Returned&&g.GuideAvailable&&g.Crates==0);Reject("solo_time_not_refunded",g,"work");
                g=Committed();Run(g,new[]{"depart guided","wait","wait"});Check("actual_failed_crossing",!g.Active&&g.Status=="failed"&&!g.Delivered&&!g.Returned&&!g.GuideAvailable);Check("failure_advice_matches_scene_contract",!g.Last.Contains("Reprepare and retry")&&g.Last.Contains("retreat"));Check("failed_work_advances_unresolved_obligation",g.Work());Check("failed_loan_deadline_retained",g.DueElapsed&&!g.Returned&&!g.Delivered);Reject("failed_return_not_assumed",g,"withdraw");Reject("failed_cannot_claim_reward",g,"complete");
                g=Committed();Run(g,new[]{"work","work","work"});Check("deadline_can_elapse",g.DueElapsed);Check("deadline_not_return_or_delivery",!g.Returned&&!g.Delivered&&!g.GuideAvailable&&g.Status=="committed");Reject("insufficient_departure_time",g,"depart guided");
                g=Committed("open");Run(g,new[]{"work","work","work"});Check("open_term_not_due",!g.DueElapsed&&!g.Delivered&&!g.Returned);
                g=new RequestExpedition();Run(g,new[]{"survey","wait","wait","wait"});Check("failed_survey_keeps_refusal",!g.Surveyed&&!g.Active&&g.Shift==1&&g.GuideAvailable);Run(g,new[]{"open"});Reject("failed_survey_no_offer",g,"hear");
                object report=new{schema_version=1,checks=new{passed=Controls.Count,failed=0},controls=Controls};string json=JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true})+"\n";if(args.Length==1)File.WriteAllText(args[0],json);else if(args.Length!=0)throw new ArgumentException("Usage: NorthStar.NarrativeChecks [REPORT]");Console.WriteLine("PASS: "+Controls.Count+" native narrative controls.");return 0;
            }
            catch(Exception error){Console.Error.WriteLine(error.Message);return 1;}
        }
    }
}
