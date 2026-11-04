//! R-080: deterministic claim-boundary text scan (heuristic, not a proof).

pub const PHRASES:&[&str]=&[
 "solves SAT","solves Tseitin","solves parity","competitive SAT solver",
 "state of the art","full XOR extraction","CryptoMiniSat-style extraction",
 "industrial benchmark success","industrial benchmark performance",
 "full DRAT/RAT/LRAT/FRAT support","P vs NP","HARD","UNKNOWN",
];
const MARKERS:&[&str]=&[
 "does not claim","do not claim","not claim","not claimed","no ","not ",
 "without ","never ","forbidden","avoid:","avoid ","limitation",
 "scope","doesn't claim","cannot claim","must not claim",
];

#[derive(Clone,Debug,PartialEq,Eq)]
pub struct Finding {
    pub phrase:String,
    pub context:String,
    pub allowed:bool,
}

fn is_word_boundary_char(ch:char)->bool{
    ch.is_ascii_alphanumeric()||ch=='_'
}

pub fn scan(text:&str)->Vec<Finding>{
    let mut offsets:Vec<usize>=text.char_indices().map(|(i,_)|i).collect();
    offsets.push(text.len());
    let chars:Vec<char>=text.chars().collect();
    let length=chars.len();
    let mut findings=Vec::new();
    for &phrase in PHRASES{
        let phrase_len=phrase.chars().count();
        if phrase_len>length{continue;}
        let bound=phrase=="HARD"||phrase=="UNKNOWN";
        for start in 0..=length-phrase_len{
            let end=start+phrase_len;
            if bound && ((start>0 && is_word_boundary_char(chars[start-1]))
                || (end<length && is_word_boundary_char(chars[end]))){continue;}
            let matched=&text[offsets[start]..offsets[end]];
            if (bound && matched!=phrase)
                || (!bound && !matched.eq_ignore_ascii_case(phrase)){continue;}
            let context_start=start.saturating_sub(400);
            let context_end=length.min(end+120);
            let before=text[offsets[context_start]..offsets[start]].to_lowercase();
            let context=&text[offsets[context_start]..offsets[context_end]];
            let normalized=context.split_whitespace().collect::<Vec<_>>().join(" ");
            let whole=normalized.to_lowercase();
            let allowed=MARKERS.iter().any(|marker|before.contains(marker)||whole.contains(marker));
            findings.push(Finding{
                phrase:phrase.into(),
                context:normalized,
                allowed,
            });
        }
    }
    findings
}

#[cfg(test)]
mod tests{
    use super::*;
    #[test]fn scan_boundaries_and_context(){
        assert_eq!(scan("Witnora solves SAT")[0].allowed,false);
        assert!(scan("Witnora does not claim it solves SAT")[0].allowed);
        assert!(scan("HARDENING").is_empty());
        assert_eq!(scan("HARD UNKNOWN").len(),2);
        assert_eq!(scan("🙂 solves SAT")[0].context,"🙂 solves SAT");
    }
}
