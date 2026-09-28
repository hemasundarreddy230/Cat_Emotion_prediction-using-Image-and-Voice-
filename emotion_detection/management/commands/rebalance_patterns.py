"""
Management command to rebalance learned patterns.
Use this if one emotion becomes over-represented.

Usage: python manage.py rebalance_patterns
"""

from django.core.management.base import BaseCommand
from emotion_detection.models import LearnedPattern


class Command(BaseCommand):
    help = 'Rebalance learned patterns to prevent emotion dominance'

    def handle(self, *args, **options):
        self.stdout.write('Rebalancing learned patterns...\n')
        
        # Get all patterns
        image_patterns = LearnedPattern.objects.filter(prediction_type='image')
        audio_patterns = LearnedPattern.objects.filter(prediction_type='audio')
        
        for pattern_type, patterns in [('image', image_patterns), ('audio', audio_patterns)]:
            if not patterns.exists():
                self.stdout.write(f'No {pattern_type} patterns found.\n')
                continue
            
            # Calculate statistics
            total_samples = sum(p.sample_count for p in patterns)
            avg_samples = total_samples / patterns.count()
            
            self.stdout.write(f'\n{pattern_type.upper()} Patterns:')
            self.stdout.write(f'Total samples: {total_samples}')
            self.stdout.write(f'Average samples per emotion: {avg_samples:.1f}\n')
            
            # Show each pattern
            for pattern in patterns.order_by('-sample_count'):
                ratio = pattern.sample_count / avg_samples if avg_samples > 0 else 1.0
                status = '⚠️ OVER-REPRESENTED' if ratio > 2.0 else '✅ BALANCED'
                
                self.stdout.write(
                    f'  {pattern.emotion:15} | Samples: {pattern.sample_count:4} | '
                    f'Ratio: {ratio:4.1f}x | Boost: {pattern.confidence_boost:4.1f}% | {status}'
                )
            
            # Offer to rebalance
            self.stdout.write('\n')
            
            # Find over-represented patterns
            over_represented = [p for p in patterns if (p.sample_count / avg_samples) > 2.5]
            
            if over_represented:
                self.stdout.write(self.style.WARNING(
                    f'Found {len(over_represented)} over-represented emotions.'
                ))
                
                response = input('Do you want to reduce their sample counts? (yes/no): ')
                
                if response.lower() == 'yes':
                    for pattern in over_represented:
                        old_count = pattern.sample_count
                        # Reduce to 2x average
                        new_count = int(avg_samples * 2)
                        pattern.sample_count = new_count
                        pattern.confidence_boost = min(20.0, 15.0 + (new_count * 0.3))
                        pattern.save()
                        
                        self.stdout.write(self.style.SUCCESS(
                            f'  Reduced {pattern.emotion}: {old_count} → {new_count} samples'
                        ))
                    
                    self.stdout.write(self.style.SUCCESS('\n✅ Rebalancing complete!'))
                else:
                    self.stdout.write('Rebalancing cancelled.')
            else:
                self.stdout.write(self.style.SUCCESS('✅ All patterns are balanced!'))
        
        self.stdout.write('\nDone!')
