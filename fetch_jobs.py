#!/usr/bin/env python3
"""Fetch genuine public job listings from configured, permitted sources.

Standard-library only. Restricted portals are intentionally not scraped.
Configure optional sources via environment variables or company_sources.json.
"""
import os, json, time, hashlib, urllib.parse, urllib.request, urllib.error, re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "jobs.json"
REGISTRY = ROOT / "company_sources.json"
ROLES = [
 "Associate Project Manager", "Project Management Associate", "Junior Project Manager",
 "PMO Analyst", "Project Coordinator", "Program Coordinator", "Project Analyst",
 "Implementation Coordinator", "Implementation Manager", "Delivery Associate",
 "Delivery Coordinator", "Scrum Master", "Customer Onboarding Manager",
 "Business Operations Associate", "Operations Analyst", "Technical Project Coordinator"
]
COUNTRIES = {"in":"India","nl":"Netherlands","de":"Germany","dk":"Denmark","se":"Sweden",
             "fi":"Finland","no":"Norway","ie":"Ireland","nz":"New Zealand"}
UA = "CareerQuestJobFetcher/1.0 (public job feeds; contact repository owner for issues)"

def now(): return datetime.now(timezone.utc).isoformat()
def request_json(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent":UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=25) as r: return json.loads(r.read().decode("utf-8"))
def request_text(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode("utf-8","replace")
def job_id(source, company, title, location, source_id=""):
    raw="|".join(map(str,[source,source_id,company,title,location])).lower()
    return hashlib.sha1(raw.encode()).hexdigest()[:18]
def norm(source, company, title, location, url, desc="", posted="", salary=None, currency="", country="Unknown", mode="Unknown", source_id=""):
    text=(title+" "+desc).lower()
    if mode=="Unknown":
        if re.search(r"\b(remote|work from home|wfh)\b",text): mode="Remote"
        elif "hybrid" in text: mode="Hybrid"
        elif re.search(r"\bon.?site\b",text): mode="Onsite"
    return {"id":job_id(source,company,title,location,source_id),"source":source,"company":company or "Company not specified",
      "title":title or "Untitled role","location":location or "Location unknown","country":country,
      "salary":salary,"currency":currency,"workMode":mode,"description":desc[:16000],"url":url,
      "posted":posted,"visaSponsorship":"Unknown","matchScore":None,"fetchedAt":now()}
def adzuna():
    app,key=os.getenv("ADZUNA_APP_ID"),os.getenv("ADZUNA_APP_KEY")
    if not app or not key: raise RuntimeError("ADZUNA_APP_ID / ADZUNA_APP_KEY not configured")
    out=[]
    for code,country in COUNTRIES.items():
      for role in ROLES:
        params=urllib.parse.urlencode({"app_id":app,"app_key":key,"what":role,"results_per_page":20,"content-type":"application/json"})
        url=f"https://api.adzuna.com/v1/api/jobs/{code}/search/1?{params}"
        try:
          data=request_json(url)
          for x in data.get("results",[]):
            loc=x.get("location",{}); place=", ".join(loc.get("display_name","").split(",")[:3])
            salary=None
            if x.get("salary_min") and x.get("salary_max"):
              salary=round(((x["salary_min"]+x["salary_max"])/2)/100000,2) if code=="in" else None
            out.append(norm("Adzuna",x.get("company",{}).get("display_name"),x.get("title"),place,x.get("redirect_url"),
              x.get("description",""),x.get("created",""),salary,"INR" if code=="in" else "",country,source_id=x.get("id","")))
          time.sleep(.12)
        except Exception as e: print(f"[Adzuna {code}/{role}] {e}")
    return out
def remoteok():
    data=request_json("https://remoteok.com/api")
    out=[]
    for x in data if isinstance(data,list) else []:
      if not x.get("id") or not x.get("position"): continue
      text=(x.get("position","")+" "+x.get("description","")).lower()
      if not any(k.lower() in text for k in ["project manager","project coordinator","pmo","implementation","delivery coordinator","operations analyst","scrum master"]): continue
      out.append(norm("Remote OK",x.get("company"),x.get("position"),"Remote",x.get("url",""),x.get("description",""),x.get("date",""),
        x.get("salary") or None,"", "Unknown","Remote",x.get("id","")))
    return out
def remotive():
    data=request_json("https://remotive.com/api/remote-jobs?search=project%20manager")
    out=[]
    for x in data.get("jobs",[]):
      out.append(norm("Remotive",x.get("company_name"),x.get("title"),x.get("candidate_required_location") or "Remote",
        x.get("url",""),x.get("description",""),x.get("publication_date",""),x.get("salary") or None,"","Unknown","Remote",x.get("id","")))
    return out
def arbeitnow():
    data=request_json("https://www.arbeitnow.com/api/job-board-api")
    out=[]
    for x in data.get("data",[]):
      title=x.get("title","")
      if not re.search(r"project|implementation|delivery|operations|scrum|pmo",title,re.I): continue
      out.append(norm("Arbeitnow",x.get("company_name"),title,x.get("location"),x.get("url",""),
        x.get("description",""),x.get("created_at",""),None,"","Germany","Remote" if x.get("remote") else "Unknown",x.get("slug","")))
    return out
def greenhouse(board):
    slug=board.get("board")
    data=request_json(f"https://boards-api.greenhouse.io/v1/boards/{urllib.parse.quote(slug)}/jobs?content=true")
    return [norm("Greenhouse · "+board["name"],board["name"],x.get("title"),x.get("location",{}).get("name"),
      x.get("absolute_url",""),x.get("content",""),x.get("updated_at",""),None,"",board.get("country","Unknown"),"Unknown",x.get("id",""))
      for x in data.get("jobs",[])]
def lever(board):
    slug=board.get("board")
    data=request_json(f"https://api.lever.co/v0/postings/{urllib.parse.quote(slug)}?mode=json")
    out=[]
    for x in data if isinstance(data,list) else []:
      cats=x.get("categories",{})
      out.append(norm("Lever · "+board["name"],board["name"],x.get("text"),cats.get("location"),x.get("hostedUrl",""),
        x.get("descriptionPlain",""),x.get("createdAt",""),None,"",board.get("country","Unknown"),"Unknown",x.get("id","")))
    return out
def load_registry():
    if not REGISTRY.exists(): return []
    try: return json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception as e: print("[registry]",e); return []
def main():
    sources=[]; all_jobs=[]
    connectors=[("Adzuna",adzuna),("Remote OK",remoteok),("Remotive",remotive),("Arbeitnow",arbeitnow)]
    registry=load_registry()
    for b in registry:
      typ=b.get("ats","").lower()
      if typ=="greenhouse": connectors.append(("Greenhouse · "+b.get("name",""),lambda b=b:greenhouse(b)))
      elif typ=="lever": connectors.append(("Lever · "+b.get("name",""),lambda b=b:lever(b)))
      else:
        sources.append({"name":b.get("name","Company source"),"status":"Configuration required","jobsFetched":0,
                        "error":"Supported public ATS: greenhouse or lever; other ATS require a permitted connector."})
    for name,fn in connectors:
      try:
        jobs=fn(); all_jobs.extend(jobs)
        sources.append({"name":name,"status":"Connected","jobsFetched":len(jobs),"lastSuccessfulFetch":now(),"error":""})
        print(f"[OK] {name}: {len(jobs)}")
      except Exception as e:
        sources.append({"name":name,"status":"Pending credentials" if "not configured" in str(e) else "Failed",
                        "jobsFetched":0,"error":str(e)[:400]})
        print(f"[FAIL] {name}: {e}")
    # Apply only the user's Indian location/work-mode/salary rules when enough data is known.
    filtered=[]
    for j in all_jobs:
      if j["country"]=="India":
        loc=j["location"].lower(); mode=j["workMode"]
        if j["salary"] is not None and j["salary"]<7: continue
        if mode=="Onsite" and "chennai" in loc: continue
        if mode=="Onsite" and not any(x in loc for x in ["bangalore","bengaluru"]): continue
        if mode=="Hybrid" and not any(x in loc for x in ["chennai","bangalore","bengaluru"]): continue
      filtered.append(j)
    dedup={}
    for j in filtered: dedup[j["id"]]=j
    jobs=list(dedup.values())
    jobs.sort(key=lambda x:x.get("posted") or x.get("fetchedAt") or "",reverse=True)
    jobs=jobs[:600]
    previous={}
    if OUT.exists():
      try: previous=json.loads(OUT.read_text(encoding="utf-8"))
      except Exception: previous={}
    # Never replace a previously populated feed with an empty result after source failures.
    if not jobs and previous.get("jobs") and all(s["status"] in ("Failed","Pending credentials") for s in sources):
      print("[WARN] all sources failed; retaining previous non-empty feed")
      return
    oldids={j.get("id") for j in previous.get("jobs",[])}
    payload={"updatedAt":now(),"newThisRun":sum(1 for j in jobs if j["id"] not in oldids),"sources":sources,"jobs":jobs}
    temp=OUT.with_suffix(".json.tmp");temp.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8");temp.replace(OUT)
    print(f"Wrote {len(jobs)} jobs; {payload['newThisRun']} new.")
if __name__=="__main__": main()
