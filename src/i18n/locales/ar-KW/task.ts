export default {
  unknownProject: 'مشروع غير معروف',
  teamMember: 'عضو الفريق',

  priority: {
    high: 'عالية',
    medium: 'متوسطة',
    low: 'منخفضة',
  },

  severity: {
    critical: 'حرجة',
    major: 'كبيرة',
    minor: 'بسيطة',
  },

  status: {
    preset: 'مبدئية',
    pending: 'قيد الانتظار',
    inProgress: 'قيد التنفيذ',
    completed: 'مكتملة',
  },

  overdue: 'متأخرة',
  moveTo: 'نقل إلى {status}',
  presetFlag: 'لم تتم مراجعتها بعد',

  assignmentCard: {
    assignedTo: 'مسندة إلى',
    reassignTo: 'إعادة الإسناد إلى',
  },

  details: {
    title: 'العنوان',
    projectDetailsTitle: 'تفاصيل المهمة',
    project: 'المشروع',
    client: 'العميل',
    completionDateTime: 'تاريخ ووقت الإنجاز',
    status: 'الحالة',
    priority: 'الأولوية',
    severity: 'الخطورة',
    startDate: 'تاريخ البدء',
    dueDate: 'تاريخ الاستحقاق',
    dueTime: 'وقت الاستحقاق',
    delete: 'حذف المهمة',
    presetFlagMessage: 'لم تتم مراجعة هذه المهمة بعد — عيّن مسؤولاً وتاريخاً.',
  },

  board: {
    noTasksTitle: 'لا توجد مهام',
    noTasksDescription: 'لا يوجد شيء هنا حالياً.',
  },

  list: {
    emptyTitle: 'لا توجد مهام مسندة',
    emptyDescription: 'ستظهر هنا المهام المسندة إليك.',
  },

  myTasksPage: {
    title: 'مهامي',
    subtitle: 'عناصر العمل المسندة إلى {name}، مرتبة حسب تاريخ الاستحقاق.',
    you: 'لك',
    addTask: 'إضافة مهمة',
  },

  tasksPage: {
    title: 'لوحة المهام',
    subtitle: 'تتبّع عناصر عمل المشروع حسب الحالة عبر الفريق.',
    myTasks: 'مهامي',
    addTask: 'إضافة مهمة',
    allPriorities: 'جميع الأولويات',
    allProjects: 'جميع المشاريع',
    allAssignees: 'جميع المكلّفين',
  },

  taskActions: {
    failedToUpdateStatus: 'فشل تحديث الحالة',
    failedToUpdatePriority: 'فشل تحديث الأولوية',
    failedToUpdateSeverity: 'فشل تحديث الخطورة',
    failedToUpdateTitle: 'فشل تحديث العنوان',
    failedToReassignTask: 'فشل إعادة إسناد المهمة',
    failedToUpdateSchedule: 'فشل تحديث الجدول الزمني',
    taskCreatedTitle: 'تم إنشاء المهمة',
    taskCreatedDescription: 'تم إسناد "{title}" إلى {assignee}.',
    failedToCreateTask: 'فشل إنشاء المهمة',
    deleteTaskTitle: 'حذف المهمة',
    deleteTaskMessage: 'حذف "{title}"؟ لا يمكن التراجع عن هذا الإجراء.',
    taskDeletedTitle: 'تم حذف المهمة',
    taskDeletedDescription: 'تم حذف "{title}".',
    failedToDeleteTask: 'فشل حذف المهمة',
  },

  formDialog: {
    title: 'إنشاء مهمة',
    taskTitle: 'عنوان المهمة',
    taskTitlePlaceholder: 'مثال: مراجعة المخططات الإنشائية',
    project: 'المشروع',
    projectPlaceholder: 'اختر المشروع',
    client: 'العميل: {name}',
    designActivity: 'نشاط التصميم (اختياري)',
    designActivityPlaceholder: 'غير مرتبط بنشاط محدد',
    assignTo: 'إسناد إلى',
    assigneeMe: '{name} (أنا)',
    priority: 'الأولوية',
    severity: 'الخطورة',
    startDate: 'تاريخ البدء (اختياري)',
    completionDate: 'تاريخ الإنجاز',
    completionTime: 'وقت الإنجاز',
    createTask: 'إنشاء مهمة',
  },

  fieldReportHistory: {
    title: 'سجل المهمة',
    emptyTitle: 'لا توجد تقارير ميدانية بعد',
    emptyDescription: 'ستظهر هنا التقارير التي راجعها مهندس الموقع لهذه المهمة.',
    by: 'بواسطة {name}',
    untitled: 'تقرير ميداني',
  },
}
