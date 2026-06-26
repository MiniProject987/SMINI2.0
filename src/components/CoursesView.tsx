import React, { useEffect, useState } from "react";
import { BookOpen, ExternalLink, Search, Loader2, Star, ArrowUpRight } from "lucide-react";
import { CourseItem } from "../types";

interface CoursesViewProps {
  token: string | null;
}

export default function CoursesView({ token }: CoursesViewProps) {
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [recommendedCareer, setRecommendedCareer] = useState<string | null>(null);
  const [salaryEstimate, setSalaryEstimate] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [platformFilter, setPlatformFilter] = useState("");
  const [difficultyFilter, setDifficultyFilter] = useState("");

  const fetchCourses = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const res = await fetch("/api/courses/recommendations", {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCourses(Array.isArray(data.recommendedCourses) ? data.recommendedCourses : []);
        setRecommendedCareer(data.recommendedCareer || null);
        setSalaryEstimate(data.salaryEstimate || null);
      }
    } catch (err) {
      console.error("Error loading courses:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, [token]);

  const filteredCourses = courses.filter(course => {
    const searchValue = search.toLowerCase();
    const matchesSearch =
      course.title.toLowerCase().includes(searchValue) ||
      course.provider.toLowerCase().includes(searchValue) ||
      (course.skillsTaught || []).some(skill => skill.toLowerCase().includes(searchValue));

    const matchesPlatform = platformFilter ? course.provider.toLowerCase().includes(platformFilter.toLowerCase()) || String(course.platform || course.source || "").toLowerCase().includes(platformFilter.toLowerCase()) : true;
    const matchesDifficulty = difficultyFilter ? course.difficulty.toLowerCase() === difficultyFilter.toLowerCase() : true;

    return matchesSearch && matchesPlatform && matchesDifficulty;
  });

  const platformLabels = Array.from(new Set(courses.map(course => course.provider || course.platform || course.source).filter(Boolean)));

  return (
    <div className="space-y-8 animate-fadeIn" id="courses-view-root">
      <div className="border-b border-gray-100 pb-5 flex flex-col sm:flex-row justify-between sm:items-center gap-4" id="courses-header">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 tracking-tight">Course Recommendations</h2>
          <p className="text-sm text-gray-500">Browse curated learning options aligned with your recommended career.</p>
          {recommendedCareer && (
            <p className="mt-2 text-xs text-slate-500">
              Recommended career: <span className="font-semibold text-slate-900">{recommendedCareer}</span>
              {salaryEstimate ? ` · Estimated salary range: ${salaryEstimate}` : ""}
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={fetchCourses}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition-all"
          >
            Refresh Courses
          </button>
        </div>
      </div>

      <div className="bg-white rounded-3xl border border-gray-100 p-5 shadow-sm" id="courses-filter-card">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by course, provider, or skill..."
              className="w-full pl-10 pr-4 py-2.5 text-xs rounded-xl border border-gray-200 focus:outline-none focus:border-indigo-400"
            />
          </div>
          <select
            value={platformFilter}
            onChange={(e) => setPlatformFilter(e.target.value)}
            className="w-full px-4 py-2.5 text-xs rounded-xl border border-gray-200 focus:outline-none focus:border-indigo-400"
          >
            <option value="">All platforms</option>
            {platformLabels.map(platform => (
              <option key={platform} value={platform}>{platform}</option>
            ))}
          </select>
          <select
            value={difficultyFilter}
            onChange={(e) => setDifficultyFilter(e.target.value)}
            className="w-full px-4 py-2.5 text-xs rounded-xl border border-gray-200 focus:outline-none focus:border-indigo-400"
          >
            <option value="">Any difficulty</option>
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
          </select>
          <div className="text-xs text-slate-500 leading-relaxed">
            Use filters to narrow by provider/platform, difficulty, and skills relevant to your recommended career.
          </div>
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-3xl border border-gray-150 p-12 text-center shadow-sm">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
          <p className="text-sm text-gray-400 mt-3">Loading course options...</p>
        </div>
      ) : filteredCourses.length === 0 ? (
        <div className="bg-white rounded-3xl border border-gray-100 p-12 text-center shadow-sm">
          <p className="text-sm text-gray-500">No courses matched your filters yet.</p>
          <p className="text-xs text-slate-400">Try a different skill or platform filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredCourses.map(course => (
            <div key={course.id} className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between" id={`course-card-${course.id}`}>
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-slate-900 font-bold text-base tracking-tight">{course.title}</h3>
                    <p className="text-[11px] uppercase tracking-wider text-slate-500 mt-1">
                      {course.provider || course.platform || course.source || "Unknown"}
                    </p>
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 bg-slate-100 border border-slate-200 rounded-full px-2 py-1">
                    {course.difficulty}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(course.skillsTaught || []).map(skill => (
                    <span key={skill} className="text-[10px] font-semibold uppercase tracking-wider bg-slate-50 border border-slate-200 rounded-full px-3 py-1 text-slate-700">
                      {skill}
                    </span>
                  ))}
                </div>
                <div className="flex items-center gap-2 text-[11px] text-slate-500">
                  <BookOpen className="w-4 h-4" />
                  <span>{course.duration}</span>
                </div>
              </div>

              <div className="mt-5 flex items-center justify-between gap-3">
                <a
                  href={course.link}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-indigo-600 text-white text-[11px] font-semibold hover:bg-indigo-700 transition-all"
                >
                  Learn More
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </a>
                {typeof course.rank === "number" && (
                  <span className="px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold uppercase tracking-wider">
                    #{course.rank}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
