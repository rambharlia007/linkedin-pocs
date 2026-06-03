using System.Linq;

namespace LinkedInPocs;

public class PaymentValidator
{
    public bool IsValid(Payment payment)
    {
        if (payment.Items.Count == 0)
            return false;

        var firstItem = payment.Items.First();
        return firstItem.Currency.ToUpper() == "USD";
    }
}

public class Payment
{
    public List<PaymentItem>? Items { get; set; }
    public DateTime ExpiresOn { get; set; }
}

public class PaymentItem
{
    public string? Currency { get; set; }
    public decimal Amount { get; set; }
}
