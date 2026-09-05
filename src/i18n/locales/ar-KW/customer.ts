export default {
  projectProgress: 'تقدم المشروع',

  projectStatus: {
    planning: 'التخطيط',
    active: 'نشط',
    onHold: 'معلّق',
    completed: 'مكتمل',
    cancelled: 'ملغى',
  },

  budgetPanel: {
    title: 'الميزانية والمدفوعات',
    emptyTitle: 'لا توجد اتفاقية مالية مسجلة',
    emptyDescription: 'ستظهر هنا تفاصيل العقد والمدفوعات بمجرد إعدادها.',
    contractAmount: 'قيمة العقد',
    paidToDate: 'المدفوع حتى الآن',
    remaining: 'المتبقي',
    upcomingPayments: 'المدفوعات القادمة',
    nothingOutstandingTitle: 'لا يوجد مستحقات',
    nothingOutstandingDescription: 'تمت تسوية جميع المدفوعات المجدولة.',
    overdue: 'متأخر',
    received: 'تم استلام {amount}',
  },

  updatesPanel: {
    title: 'آخر التحديثات',
    emptyTitle: 'لا توجد تحديثات بعد',
    emptyDescription: 'ستظهر هنا آخر أنشطة المشروع مع تقدم العمل.',
  },

  activitiesPanel: {
    title: 'نطاق العمل',
    emptyTitle: 'لا توجد أنشطة مسجلة',
    emptyDescription: 'ستظهر هنا الأنشطة المحددة التي يشملها هذا التعاقد بمجرد إعدادها.',
  },

  milestoneTimeline: {
    title: 'مراحل المشروع',
    emptyTitle: 'لا توجد مراحل بعد',
    emptyDescription: 'ستظهر هنا مراحل المشروع بمجرد إعداد خطة المشروع.',
    due: 'الاستحقاق:',
    completed: 'الإنجاز:',
    overdue: 'متأخر',
  },

  milestoneStatus: {
    completed: 'مكتمل',
    inProgress: 'قيد التنفيذ',
    delayed: 'متأخر',
    upcoming: 'قادم',
  },

  deliverablesPanel: {
    title: 'المخرجات',
    completedCount: '{completed}/{total} مكتمل ({rate}%)',
    emptyTitle: 'لا توجد مخرجات بعد',
    emptyDescription: 'ستظهر هنا الرسومات والتقارير والمخرجات الأخرى عند مشاركتها.',
    type: 'النوع:',
    delivered: 'تاريخ التسليم:',
    approved: 'تاريخ الاعتماد:',
  },

  deliverableStatus: {
    pending: 'قيد الانتظار',
    delivered: 'تم التسليم',
    approved: 'معتمد',
    revision: 'قيد المراجعة',
  },

  header: {
    client: 'العميل:',
    overallProgress: 'التقدم الإجمالي',
    startDate: 'تاريخ البدء',
    expectedCompletion: 'الإنجاز المتوقع',
    actualCompletion: 'الإنجاز الفعلي',
    daysRemaining: 'متبقٍ {count} يومًا',
    targetDatePassed: 'تجاوز التاريخ المستهدف',
  },

  loginPage: {
    title: 'تتبّع مشروعك',
    subtitle: 'سجّل الدخول برقم عميلك لعرض التقدم الحي والمعالم والمخرجات.',
    idLabel: 'رقم العميل',
    idPlaceholder: 'أدخل رقم عميلك',
    footerNotice: 'أنت فقط من يمكنه عرض مشروعك، بعد التحقق من رقم عميلك وكلمة المرور.',
  },

  projectsPage: {
    noProjectsFound: 'لا توجد مشاريع',
    noProjectsFoundDescription: 'لا توجد مشاريع مرتبطة بحسابك بعد. يرجى التواصل مع مهندس مشروعك.',
    checkAgain: 'تحقق مجددًا',
    yourProjects: 'مشاريعك',
    projectIdLabel: 'معرّف المشروع: {id}',
  },

  projectViewPage: {
    projectStatus: 'حالة المشروع',
    projectIdLabel: 'معرّف المشروع: {id}',
    refresh: 'تحديث',
    needHelp: 'بحاجة إلى مساعدة؟',
    projectEngineer: 'مهندس المشروع',
    supportEmail: 'البريد الإلكتروني للدعم',
    milestones: 'المعالم',
    milestonesCompleted: '{completed}/{total} مكتمل',
    deliverables: 'المخرجات',
    deliverablesApproved: '{approved}/{total} معتمد',
    disclaimer: 'للأمور السرية أو المناقشات التفصيلية، يرجى التواصل مباشرة مع مكتب إدارة المشاريع.',
    unableToLoad: 'تعذّر تحميل هذا المشروع.',
  },
}
