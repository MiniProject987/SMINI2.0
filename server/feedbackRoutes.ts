/**
 * User Feedback & Testing Module
 * Collects user feedback, pilot study data, and generates analysis reports
 * Integrated into the Smart Career Advisor backend
 */

import { Router, Request, Response } from "express";
import path from "path";
import { db } from "./db.js";

export const feedbackRoutes = Router();

interface FeedbackSubmission {
  userId: string;
  type: "bug" | "feature" | "improvement" | "other";
  category: string;
  rating: number; // 1-5
  title: string;
  description: string;
  timestamp: string;
  pageContext?: string;
  resolved?: boolean;
}

interface PilotStudyResponse {
  userId: string;
  studyPhase: number;
  questionId: string;
  rating: number; // 1-5
  feedback: string;
  completedAt: string;
}

interface FeedbackStats {
  totalSubmissions: number;
  averageRating: number;
  feedbackByType: Record<string, number>;
  feedbackByCategory: Record<string, number>;
  pilotStudyProgress: number;
  pilotStudyParticipants: number;
}

/**
 * Middleware: Ensure user is authenticated
 */
function authenticateFeedback(req: Request, res: Response, next: Function) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  const token = authHeader.split(" ")[1];
  const user = db.users.findOne(u => `token_${u.id}` === token || token === "token-admin");
  if (!user) {
    return res.status(401).json({ error: "Invalid token" });
  }
  (req as any).user = user;
  next();
}

/**
 * GET /api/feedback/status
 * Check if user has already provided feedback in this session
 */
feedbackRoutes.get("/api/feedback/status", authenticateFeedback, (req: Request, res: Response) => {
  const user = (req as any).user;
  
  // Check if feedback submission table exists
  if (!db.userFeedback) {
    return res.json({
      hasFeedback: false,
      sessionFeedbackCount: 0,
    });
  }

  const userFeedback = db.userFeedback.find((f: FeedbackSubmission) => f.userId === user.id);
  const sessionFeedback = userFeedback.filter((f: FeedbackSubmission) => {
    const submittedDate = new Date(f.timestamp).toDateString();
    const today = new Date().toDateString();
    return submittedDate === today;
  });

  res.json({
    hasFeedback: userFeedback.length > 0,
    sessionFeedbackCount: sessionFeedback.length,
    totalFeedbackCount: userFeedback.length,
  });
});

/**
 * POST /api/feedback/submit
 * Submit user feedback (bug report, feature request, improvement suggestion, etc.)
 */
feedbackRoutes.post("/api/feedback/submit", authenticateFeedback, (req: Request, res: Response) => {
  const user = (req as any).user;
  const { type, category, rating, title, description, pageContext } = req.body;

  // Validation
  if (!type || !category || !rating || !title || !description) {
    return res.status(400).json({ error: "Missing required feedback fields" });
  }

  if (rating < 1 || rating > 5) {
    return res.status(400).json({ error: "Rating must be between 1 and 5" });
  }

  // Initialize feedback table if needed
  if (!db.userFeedback) {
    db.userFeedback = [];
  }

  // Create feedback submission
  const feedback: FeedbackSubmission = {
    userId: user.id,
    type: type as "bug" | "feature" | "improvement" | "other",
    category,
    rating: parseInt(rating),
    title,
    description,
    pageContext: pageContext || "unknown",
    timestamp: new Date().toISOString(),
    resolved: false,
  };

  // Store feedback (normally would use db.userFeedback.insert())
  db.userFeedback.push(feedback);

  console.log(`[Feedback] ${user.name} submitted ${type}: "${title}"`);

  res.status(201).json({
    success: true,
    feedbackId: `feedback_${Date.now()}`,
    message: "Thank you for your feedback!",
    feedback,
  });
});

/**
 * GET /api/feedback/history
 * Get user's own feedback submissions
 */
feedbackRoutes.get("/api/feedback/history", authenticateFeedback, (req: Request, res: Response) => {
  const user = (req as any).user;

  if (!db.userFeedback) {
    return res.json([]);
  }

  const userFeedback = db.userFeedback.filter((f: FeedbackSubmission) => f.userId === user.id);
  res.json(userFeedback);
});

/**
 * POST /api/pilot-study/enroll
 * Enroll user in pilot study
 */
feedbackRoutes.post("/api/pilot-study/enroll", authenticateFeedback, (req: Request, res: Response) => {
  const user = (req as any).user;

  if (!db.pilotStudyParticipants) {
    db.pilotStudyParticipants = [];
  }

  // Check if already enrolled
  const existing = db.pilotStudyParticipants.find((p: any) => p.userId === user.id);
  if (existing) {
    return res.status(400).json({ error: "User already enrolled in pilot study" });
  }

  const enrollment = {
    userId: user.id,
    enrolledAt: new Date().toISOString(),
    phase: 1,
    status: "active",
    completedSurveys: 0,
  };

  db.pilotStudyParticipants.push(enrollment);

  res.status(201).json({
    success: true,
    message: "Successfully enrolled in pilot study",
    enrollment,
  });
});

/**
 * POST /api/pilot-study/submit-response
 * Submit response to pilot study questionnaire
 */
feedbackRoutes.post("/api/pilot-study/submit-response", authenticateFeedback, (req: Request, res: Response) => {
  const user = (req as any).user;
  const { studyPhase, questionId, rating, feedback } = req.body;

  if (!studyPhase || !questionId || !rating) {
    return res.status(400).json({ error: "Missing required pilot study fields" });
  }

  if (!db.pilotStudyResponses) {
    db.pilotStudyResponses = [];
  }

  const response: PilotStudyResponse = {
    userId: user.id,
    studyPhase: parseInt(studyPhase),
    questionId,
    rating: parseInt(rating),
    feedback: feedback || "",
    completedAt: new Date().toISOString(),
  };

  db.pilotStudyResponses.push(response);

  // Update participant survey count
  if (db.pilotStudyParticipants) {
    const participant = db.pilotStudyParticipants.find((p: any) => p.userId === user.id);
    if (participant) {
      participant.completedSurveys = (participant.completedSurveys || 0) + 1;
    }
  }

  console.log(`[Pilot Study] ${user.name} submitted response for phase ${studyPhase}`);

  res.status(201).json({
    success: true,
    message: "Response recorded",
    response,
  });
});

/**
 * GET /api/pilot-study/progress
 * Get user's pilot study progress
 */
feedbackRoutes.get("/api/pilot-study/progress", authenticateFeedback, (req: Request, res: Response) => {
  const user = (req as any).user;

  if (!db.pilotStudyParticipants) {
    return res.status(404).json({ error: "User not enrolled in pilot study" });
  }

  const participant = db.pilotStudyParticipants.find((p: any) => p.userId === user.id);
  if (!participant) {
    return res.status(404).json({ error: "User not enrolled in pilot study" });
  }

  const responses = db.pilotStudyResponses
    ? db.pilotStudyResponses.filter((r: PilotStudyResponse) => r.userId === user.id)
    : [];

  res.json({
    enrollment: participant,
    responsesSubmitted: responses.length,
    lastResponseAt: responses.length > 0 ? responses[responses.length - 1].completedAt : null,
  });
});

/**
 * GET /api/feedback/analytics
 * Get aggregate feedback statistics (admin endpoint)
 */
feedbackRoutes.get("/api/feedback/analytics", authenticateFeedback, (req: Request, res: Response) => {
  const user = (req as any).user;

  // Simple admin check (in production, use proper role-based access)
  if (user.role !== "admin" && user.email !== "admin@example.com") {
    return res.status(403).json({ error: "Unauthorized" });
  }

  const stats: FeedbackStats = {
    totalSubmissions: db.userFeedback ? db.userFeedback.length : 0,
    averageRating: 0,
    feedbackByType: {},
    feedbackByCategory: {},
    pilotStudyProgress: 0,
    pilotStudyParticipants: db.pilotStudyParticipants ? db.pilotStudyParticipants.length : 0,
  };

  // Calculate feedback statistics
  if (db.userFeedback && db.userFeedback.length > 0) {
    const ratings = db.userFeedback.map((f: FeedbackSubmission) => f.rating);
    stats.averageRating = ratings.reduce((a: number, b: number) => a + b, 0) / ratings.length;

    // Count by type
    db.userFeedback.forEach((f: FeedbackSubmission) => {
      stats.feedbackByType[f.type] = (stats.feedbackByType[f.type] || 0) + 1;
      stats.feedbackByCategory[f.category] = (stats.feedbackByCategory[f.category] || 0) + 1;
    });
  }

  // Calculate pilot study completion
  if (db.pilotStudyResponses && db.pilotStudyParticipants) {
    const totalPossibleResponses = db.pilotStudyParticipants.length * 3; // 3 phases
    stats.pilotStudyProgress = (db.pilotStudyResponses.length / totalPossibleResponses) * 100;
  }

  res.json(stats);
});

/**
 * GET /api/feedback/analytics/export
 * Export feedback analytics as CSV
 */
feedbackRoutes.get("/api/feedback/analytics/export", authenticateFeedback, (req: Request, res: Response) => {
  const user = (req as any).user;

  if (user.role !== "admin" && user.email !== "admin@example.com") {
    return res.status(403).json({ error: "Unauthorized" });
  }

  if (!db.userFeedback || db.userFeedback.length === 0) {
    return res.status(400).json({ error: "No feedback data to export" });
  }

  // Generate CSV
  const headers = ["Timestamp", "User ID", "Type", "Category", "Rating", "Title", "Description", "Page Context"];
  const rows = db.userFeedback.map((f: FeedbackSubmission) => [
    f.timestamp,
    f.userId,
    f.type,
    f.category,
    f.rating,
    `"${f.title}"`,
    `"${f.description.substring(0, 100)}"`,
    f.pageContext,
  ]);

  const csv = [headers, ...rows].map(row => row.join(",")).join("\n");

  res.setHeader("Content-Type", "text/csv");
  res.setHeader("Content-Disposition", 'attachment; filename="feedback_export.csv"');
  res.send(csv);
});

/**
 * GET /api/feedback/report
 * Generate comprehensive feedback report
 */
feedbackRoutes.get("/api/feedback/report", authenticateFeedback, (req: Request, res: Response) => {
  const user = (req as any).user;

  if (user.role !== "admin" && user.email !== "admin@example.com") {
    return res.status(403).json({ error: "Unauthorized" });
  }

  const feedbackList = db.userFeedback || [];
  const pilotParticipants = db.pilotStudyParticipants || [];
  const pilotResponses = db.pilotStudyResponses || [];

  // Analyze feedback
  const analysis = {
    timestamp: new Date().toISOString(),
    totalFeedbackSubmissions: feedbackList.length,
    averageRating: feedbackList.length > 0 ? (feedbackList.reduce((sum: number, f: FeedbackSubmission) => sum + f.rating, 0) / feedbackList.length) : 0,
    feedbackByType: {} as Record<string, number>,
    feedbackByCategory: {} as Record<string, number>,
    highPriorityIssues: feedbackList.filter((f: FeedbackSubmission) => f.rating <= 2).map(f => ({
      type: f.type,
      title: f.title,
      rating: f.rating,
    })),
    pilotStudy: {
      totalParticipants: pilotParticipants.length,
      totalResponses: pilotResponses.length,
      averagePhaseRating: pilotResponses.length > 0 ? (pilotResponses.reduce((sum: number, r: PilotStudyResponse) => sum + r.rating, 0) / pilotResponses.length) : 0,
      responsesByPhase: {} as Record<number, number>,
    },
  };

  // Count by type and category
  feedbackList.forEach((f: FeedbackSubmission) => {
    analysis.feedbackByType[f.type] = (analysis.feedbackByType[f.type] || 0) + 1;
    analysis.feedbackByCategory[f.category] = (analysis.feedbackByCategory[f.category] || 0) + 1;
  });

  // Count pilot study responses by phase
  pilotResponses.forEach((r: PilotStudyResponse) => {
    analysis.pilotStudy.responsesByPhase[r.studyPhase] = (analysis.pilotStudy.responsesByPhase[r.studyPhase] || 0) + 1;
  });

  res.json(analysis);
});

export default feedbackRoutes;
